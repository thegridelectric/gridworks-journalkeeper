import os
from typing import Dict, List

import dotenv
import pendulum
from sqlalchemy import asc, create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.enums import TelemetryName
from gjk.first_season.beech_channels import BEECH_CHANNELS_BY_NAME
from gjk.models import (
    DataChannelSql,
    NodalHourlyEnergySql,
    ReadingSql,
    bulk_insert_nodal_hourly_energy,
)


def add_to_nodal_hourly_energy_table(
    session,
    start: pendulum.DateTime = None,
    end: pendulum.DateTime = pendulum.now(),
    time_delta: int = 10,
    record_zeros: bool = True,
):
    """
    Computes hourly energy consumption within the specified timeframe from power data in the specified session.
    Inserts the results into the `nodal_hourly_energy` table which tracks the device-by-device energy
    use within a heat pump thermal storage terminal asset.

    If the hour has negative energy, nothing is recorded

    Parameters:
    - session: The database session from which the power data is read and to which the energy data will be inserted.
    - start (pendulum.DateTime, optional): The start datetime for the period to compute energy. Defaults to None.
    - end (pendulum.DateTime, optional): The end datetime for the period to compute energy. Defaults to the current time.
    - time_delta (int, optional): If start is not specified, the number of hours prior to the end time to process. Defaults to 10 hours.
    - record_zeros: if the hour has 0 energy, record this

    Returns:
    - None: This function does not return any value. It performs an insert operation into the database.
    """

    floating_zero_power_watts = -2.5

    # If there is no specified start time, use the time_delta
    if start is None:
        start = end.add(hours=-time_delta)
        if time_delta <= 0:
            raise ValueError("time_detla must be a positive integer")

    start = start.replace(minute=0, second=0, microsecond=0)
    end = end.replace(minute=0, second=0, microsecond=0)

    print(f"\nStart: {start}\nEnd: {end}\n")

    if start >= end:
        raise ValueError("The start time must be earlier than the end time.")

    # ------------------------------------------
    # Import power readings by channel
    # ------------------------------------------

    # Convert to Unix timestamp in milliseconds
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    # Store the readings by channel in a dictionnary
    power_channels = [
        channel
        for channel in BEECH_CHANNELS_BY_NAME.values()
        if channel.telemetry_name == TelemetryName.PowerW.value
    ]
    power_readings: Dict[DataChannelSql, List[ReadingSql]] = {}
    for channel in power_channels:
        power_readings[channel] = (
            session.query(ReadingSql)
            .filter(
                ReadingSql.time_ms >= start_ms,
                ReadingSql.time_ms < end_ms,
                ReadingSql.data_channel_id == channel.id,
            )
            .order_by(asc(ReadingSql.time_ms))
            .all()
        )

    # ------------------------------------------
    # For every hour, convert to energy
    # ------------------------------------------

    energy_results = {}
    num_hours = int((end - start).total_hours())

    for channel in power_channels:
        energy_results[channel] = []
        time_data_hours = [
            pendulum.from_timestamp(x.time_ms / 1000).replace(
                minute=0, second=0, microsecond=0
            )
            for x in power_readings[channel]
        ]

        # Find the last power value recorded before the requested start time
        past_days = 60
        past_power_readings: List[ReadingSql] = (
            session.query(ReadingSql)
            .filter(
                ReadingSql.time_ms
                >= int(start.add(hours=-past_days * 24).timestamp() * 1000),
                ReadingSql.time_ms < start_ms,
                ReadingSql.data_channel_id == channel.id,
            )
            .order_by(asc(ReadingSql.time_ms))
            .all()
        )
        if past_power_readings:
            last_power_before_current_hour = past_power_readings[-1].value
        else:
            last_power_before_current_hour = 0
            print(
                f"No data for {channel.name} has been found within the {past_days} days before start datetime. Assuming no power just before the start datetime."
            )

        for hour in range(num_hours):
            current_hour = start.add(hours=hour)
            next_hour = start.add(hours=hour + 1)

            # Isolate data for the given hour
            times_for_this_hour = [
                r.time_ms
                for i, r in enumerate(power_readings[channel])
                if time_data_hours[i] == current_hour
            ]
            powers_for_this_hour = [
                r.value
                for i, r in enumerate(power_readings[channel])
                if time_data_hours[i] == current_hour
            ]

            # Add points at the start and end of the hour
            times_for_this_hour = (
                [current_hour.timestamp() * 1000]
                + times_for_this_hour
                + [next_hour.timestamp() * 1000]
            )
            if powers_for_this_hour:
                powers_for_this_hour = (
                    [last_power_before_current_hour]
                    + powers_for_this_hour
                    + [powers_for_this_hour[-1]]
                )
                last_power_before_current_hour = powers_for_this_hour[
                    -1
                ]  # for the next hour
            else:
                powers_for_this_hour = (
                    [last_power_before_current_hour]
                    + powers_for_this_hour
                    + [last_power_before_current_hour]
                )

            # Treat negative power values
            for i in range(len(powers_for_this_hour)):
                if powers_for_this_hour[i] < 0:
                    if powers_for_this_hour[i] > floating_zero_power_watts:
                        powers_for_this_hour[i] = 0
                    else:
                        print(
                            f"The value for {channel.name} at time {times_for_this_hour[i]} is "
                            f" {powers_for_this_hour[i]} W. Assume the CT is backwards and making positive"
                        )
                        powers_for_this_hour[i] = -powers_for_this_hour[i]
                        # raise ValueError(f"The value for {channel.name} at time {times_for_this_hour[i]} is {powers_for_this_hour[i]} W")

            # Compute the energy for the given hour
            time_diff_hours = [
                (y - x) / 1000 / 60 / 60
                for x, y in zip(times_for_this_hour[:-1], times_for_this_hour[1:])
            ]
            energy = round(
                sum([
                    powers_for_this_hour[i] * time_diff_hours[i]
                    for i in range(len(time_diff_hours))
                ]),
                2,
            )
            energy_results[channel].append(energy)

    # ------------------------------------------
    # Add the results to the database
    # ------------------------------------------

    # Create a list of NodalHourlyEnergySql objects to insert
    nodal_hourly_energy_list = []

    for h in range(num_hours):
        for channel in power_channels:
            ta_alias = channel.terminal_asset_alias
            hour_start = int(start.add(hours=h).timestamp())
            value = int(energy_results[channel][h])
            id = f"{channel.name}_{hour_start}_{ta_alias}"

            if value > 0 or record_zeros:
                nodal_hourly_energy = NodalHourlyEnergySql(
                    id=id,
                    hour_start_s=hour_start,
                    power_channel_id=channel.id,
                    watt_hours=value,
                )

                nodal_hourly_energy_list.append(nodal_hourly_energy)
    print(
        f"\nSuccessfully created a list of {len(nodal_hourly_energy_list)} NodalHourlyEnergySql objects to add to the database.\n"
    )

    bulk_insert_nodal_hourly_energy(session, nodal_hourly_energy_list)


if __name__ == "__main__":
    dotenv.load_dotenv()
    engine = create_engine(os.getenv("GJK_DB_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()

    timezone = "America/New_York"
    start = pendulum.datetime(2024, 2, 1, 0, 0, tz=timezone)
    end = pendulum.datetime(2024, 2, 2, 20, 0, tz=timezone)

    add_to_nodal_hourly_energy_table(session=session, start=start, end=end)
