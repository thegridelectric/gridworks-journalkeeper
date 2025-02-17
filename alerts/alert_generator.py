import json
import time
import dotenv
import pendulum
import requests
from gjk.api_db import get_db
from gjk.config import Settings
from gjk.models import MessageSql
from sqlalchemy import asc, or_
from sqlalchemy.exc import SQLAlchemyError

class AlertGenerator():

    def __init__(self):
        self.opsgenie_team_id = "edaccf48-a7c9-40b7-858a-7822c6f862a4"
        self.settings = Settings(_env_file=dotenv.find_dotenv())
        self.timezone_str = 'America/New_York'
        self.ignored_house_aliases = ['maple'] # TODO: put this in the .env file
        self.max_time_no_data = 10*60 #TODO nyquist
        self.main_loop_seconds = 5*60
        self.hours_back = 1
        self.max_setpoint_violation_f = 2
        self.min_dist_pump_kw = 2
        self.min_dist_pump_gpm = 0.5
        self.data = {}
        self.alert_status = {}
        self.main()

    def send_opsgenie_alert(self, message, alias, priority="P1"):
        print(f"- [ALERT] {message}")
        url = "https://api.opsgenie.com/v2/alerts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"GenieKey {self.settings.ops_genie_api_key.get_secret_value()}",
        }
        responders = [{"type": "team", "id": self.opsgenie_team_id}]
        payload = {
            "message": message,
            "alias": f"{pendulum.now(tz=self.timezone_str)}-{alias}",
            "priority": priority,
            "responders": responders,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 202:
            print("Alert sent successfully")
        else:
            print(f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}")

    def unix_ms_to_date(self, time_ms):
        return pendulum.from_timestamp(time_ms/1000, tz=self.timezone_str).replace(second=0, microsecond=0)

    def get_data_from_journaldb(self):
        print("\nFinding data from journaldb...")
        try:
            with next(get_db()) as session:
                start_ms = pendulum.now(tz="America/New_York").add(hours=-self.hours_back).timestamp() * 1000
                self.messages = (
                    session.query(MessageSql).filter(
                        MessageSql.message_type_name == "report",
                        MessageSql.message_persisted_ms >= start_ms,
                        ).order_by(asc(MessageSql.message_persisted_ms)).all()
                    )
                if not self.messages:
                    raise Exception("No messages found.")
        except Exception as e:
            print(f"An error occured while getting data from journaldb: {e}")
            return
        
        all_house_aliases = list({x.from_alias.split(".")[-2] for x in self.messages})
        self.selected_house_aliases = [x for x in all_house_aliases if x not in self.ignored_house_aliases]

        for house_alias in all_house_aliases:
                        
            if house_alias not in self.alert_status:
                self.alert_status[house_alias] = {}
            
            self.data[house_alias] = {}

            if house_alias not in self.selected_house_aliases:
                print(f"- {house_alias}: House is not in the selected aliases")
                continue

            for message in [m for m in self.messages if house_alias in m.from_alias]:
                for channel in message.payload["ChannelReadingList"]:
                    channel_name = channel["ChannelName"]
                    if channel_name not in self.data[house_alias]:
                        self.data[house_alias][channel_name] = {
                            "values": channel["ValueList"],
                            "times": channel["ScadaReadTimeUnixMsList"],
                        }
                    else:
                        self.data[house_alias][channel_name]["values"].extend(channel["ValueList"])
                        self.data[house_alias][channel_name]["times"].extend(channel["ScadaReadTimeUnixMsList"])

            for channel in self.data[house_alias].keys():
                sorted_times_values = sorted(zip(self.data[house_alias][channel]["times"], self.data[house_alias][channel]["values"]))
                sorted_times, sorted_values = zip(*sorted_times_values)
                self.data[house_alias][channel]["times"] = list(sorted_times)
                self.data[house_alias][channel]["values"] = list(sorted_values)

            if self.data[house_alias]:
                print(f"- {house_alias}: Found data")
            else:
                print(f"- {house_alias}: Did not find any data")
                self.check_no_data()

    def check_no_data(self):
        alert_alias = "no_data"
        print("\nChecking for data...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = False

            most_recent_ms = 0
            for channel in self.data[house_alias]:
                if self.data[house_alias][channel]['times'][-1] > most_recent_ms:
                    most_recent_ms = self.data[house_alias][channel]['times'][-1]

            if not self.data[house_alias]:
                if not self.alert_status[house_alias][alert_alias]:
                    alert_message = f"{house_alias}: No data found in the last {self.hours_back} hour(s)"
                    self.send_opsgenie_alert(alert_message, alert_alias)
                    self.alert_status[house_alias][alert_alias] = True

            elif time.time() - most_recent_ms/1000 > self.max_time_no_data:
                if not self.alert_status[house_alias][alert_alias]:
                    alert_message = f"{house_alias}: No data coming in since {round((time.time()-most_recent_ms/1000)/60,1)} minutes"
                    self.send_opsgenie_alert(alert_message, alert_alias)
                    self.alert_status[house_alias][alert_alias] = True

            else:
                print(f"- {house_alias}: Found data up to {round((time.time()-most_recent_ms/1000)/60,1)} minutes ago")
                self.alert_status[house_alias][alert_alias] = False

    def check_zone_below_setpoint(self):
        alert_alias = "zone_setpoint"
        print("\nChecking for zones below setpoint...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = {}
            print(f"- {house_alias}:")

            channels_by_zone = {}
            for channel in [x for x in self.data[house_alias] if 'zone' in x]:
                if channel[:5] not in channels_by_zone:
                    channels_by_zone[channel[:5]] = []
                channels_by_zone[channel[:5]].append(channel)

            for zone in channels_by_zone:
                if zone not in self.alert_status[house_alias][alert_alias]:
                    self.alert_status[house_alias][alert_alias][zone] = False

                for channel in channels_by_zone[zone]:
                    if "set" in channel:
                        setpoint = self.data[house_alias][channel]["values"][-1] / 1000
                    if "temp" in channel and "gw" not in channel:
                        temperature = self.data[house_alias][channel]["values"][-1] / 1000

                if setpoint - temperature < self.max_setpoint_violation_f:
                    print(f"-- {zone} is close to or above setpoint")
                    self.alert_status[house_alias][alert_alias][zone] = False
                else:                    
                    # Check for a recent setpoint increase 
                    setpoint_channel: str = [x for x in channels_by_zone[zone] if "set" in x][0]
                    if len(set(self.data[house_alias][setpoint_channel]["values"])) == 1:
                        if not self.alert_status[house_alias][alert_alias][zone]:
                            alert_message = f"{house_alias}: {setpoint_channel.replace('-set','')} is significantly below setpoint"
                            self.send_opsgenie_alert(alert_message, alert_alias)
                            self.alert_status[house_alias][alert_alias][zone] = True
                    else:
                        setpoint_values = self.data[house_alias][setpoint_channel]["values"]
                        if min(setpoint_values) < setpoint_values[-1] and min(setpoint_values)-temperature < self.max_setpoint_violation_f:
                            print(f"-- {zone} is significantly below setpoint but the setpoint was increased recently")
                        else:
                            if not self.alert_status[house_alias][alert_alias][zone]:
                                alert_message = f"{house_alias}: {setpoint_channel.replace('-set','')} is significantly below setpoint"
                                self.send_opsgenie_alert(alert_message, alert_alias)
                                self.alert_status[house_alias][alert_alias][zone] = True

    def check_dist_pump(self):
        alert_alias = "dist_pump"
        print("\nChecking for distribution pump activity...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = 0

            last_heatcall_time = 0
            for zone_state in [x for x in self.data[house_alias] if 'zone' in x and 'state' in x]:
                channel = self.data[house_alias][zone_state]
                zone_heatcall_times = [t for t, state in zip(channel['times'], channel['values']) if state==1]
                if zone_heatcall_times:
                    zone_last_heatcall_time = zone_heatcall_times[-1]
                else:
                    continue
                if zone_last_heatcall_time > last_heatcall_time:
                    last_heatcall_time = zone_last_heatcall_time

            if (not [x for x in self.data[house_alias] if 'zone' in x and 'state' in x] 
                or 'dist-pump-pwr' not in self.data[house_alias]):
                print(f"{house_alias}: Missing data!") # TODO: create an alert?
                continue

            if last_heatcall_time == 0:
                print(f"{house_alias}: No recent heat call")
                continue

            # Try to find power around the latest heat call
            pwr = self.data[house_alias]['dist-pump-pwr']
            power_around_heatcall = [
                power for time, power in zip(pwr['times'], pwr['values']) 
                if time >= last_heatcall_time - 5*60*1000
            ]
            if not power_around_heatcall and pwr['values'][-1] <= self.min_dist_pump_kw:
                print(f"- {house_alias}: No pump power recorded around heat call and latest power is low")
                self.alert_status[house_alias][alert_alias] += 1
            elif max(power_around_heatcall) <= self.min_dist_pump_kw:
                print(f"- {house_alias}: No significant pump power around heat call")
                self.alert_status[house_alias][alert_alias] += 1
            else:
                print(f"- {house_alias}: Found dist pump power after last heat call")
                self.alert_status[house_alias][alert_alias] = 0
                continue

            # Try to find flow around the latest heat call
            flow = self.data[house_alias]['dist-flow']
            flow_around_heatcall = [
                flow/100 for time, flow in zip(flow['times'], flow['values']) 
                if time >= last_heatcall_time - 5*60*1000
            ]
            if not flow_around_heatcall and flow['values'][-1] <= self.min_dist_pump_gpm:
                print(f"- {house_alias}: No pump flow recorded around heat call and latest flow is low")
            elif max(flow_around_heatcall) <= self.min_dist_pump_gpm:
                print(f"- {house_alias}: No significant pump flow around heat call")
            else:
                print(f"- {house_alias}: Found dist pump flow after last heat call")
                self.alert_status[house_alias][alert_alias] = 0
                continue

            if self.alert_status[house_alias][alert_alias] == 3:
                alert_message = f"{house_alias}: No distribution pump activity recorded since the last heat call"
                self.send_opsgenie_alert(alert_message, alert_alias)
    
    def check_store_pump(self):
        alert_alias = "store_pump"
        print("\nChecking for store pump activity...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = 0


    def main(self):
        while True:
            self.get_data_from_journaldb()
            self.check_no_data()
            self.check_zone_below_setpoint()
            self.check_dist_pump()
            # self.check_store_pump()
            # self.check_hp()
            # self.check_in_atn()
            # self.check_hp_on_during_onpeak()
            time.sleep(self.main_loop_seconds)


if __name__ == '__main__':
    a = AlertGenerator()