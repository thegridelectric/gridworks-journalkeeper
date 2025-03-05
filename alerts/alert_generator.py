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
        self.ignored_house_aliases = ['moss'] # TODO: put this in the .env file
        self.max_time_no_data = 10*60 #TODO nyquist
        self.main_loop_seconds = 5*60
        self.hours_back = 2
        self.max_setpoint_violation_f = 2
        self.min_dist_pump_w = 2
        self.min_store_pump_w = 5
        self.min_dist_pump_gpm = 0.5
        self.min_store_pump_gpm = 0.5
        self.min_hp_kw = 1
        self.on_peak_hours = [7,8,9,10,11,16,17,18,19]
        self.data = {}
        self.relays = {}
        self.alert_status = {}
        self.main()

    def send_opsgenie_alert(self, message, house_alias, alert_alias, unique_alias=False, priority="P1"):
        print(f"- [ALERT] {message}")
        url = "https://api.opsgenie.com/v2/alerts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"GenieKey {self.settings.ops_genie_api_key.get_secret_value()}",
        }
        responders = [{"type": "team", "id": self.opsgenie_team_id}]
        alias = f"{pendulum.now(tz=self.timezone_str).format('YYYY-MM-DD')}-{house_alias}-{alert_alias}"
        if unique_alias:
            alias = f"{pendulum.now(tz=self.timezone_str).format('YYYY-MM-DD-HH-mm')}-{house_alias}-{alert_alias}"
        payload = {
            "message": message,
            "alias": alias,
            "priority": priority,
            "responders": responders,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 202:
            print("Alert sent successfully")
        else:
            print(f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}")

    def unix_ms_to_date(self, time_ms):
        return pendulum.from_timestamp(time_ms/1000, tz=self.timezone_str).replace(microsecond=0)

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
            self.relays[house_alias] = {}

            if house_alias not in self.selected_house_aliases:
                print(f"- {house_alias}: House is not in the selected aliases")
                continue

            for message in [m for m in self.messages if m.from_alias.split(".")[-2] == house_alias]:
                for channel in message.payload["ChannelReadingList"]:
                    channel_name = channel["ChannelName"]
                    if channel_name not in self.data[house_alias]:
                        self.data[house_alias][channel_name] = {}
                        self.data[house_alias][channel_name]['times'] = []
                        self.data[house_alias][channel_name]['values'] = []
                    self.data[house_alias][channel_name]["times"].extend(channel["ScadaReadTimeUnixMsList"])
                    self.data[house_alias][channel_name]["values"].extend(channel["ValueList"])

                    if "StateList" in message.payload:
                        for state in message.payload["StateList"]:
                            if 'relay' in state["MachineHandle"]:
                                relay_name = state["MachineHandle"].split('.')[-1]
                                if relay_name not in self.relays[house_alias]:
                                    self.relays[house_alias][relay_name] = {}
                                if state["MachineHandle"] not in self.relays[house_alias][relay_name]:
                                    self.relays[house_alias][relay_name][state["MachineHandle"]] = {}
                                    self.relays[house_alias][relay_name][state["MachineHandle"]]["times"] = []
                                    self.relays[house_alias][relay_name][state["MachineHandle"]]["values"] = []
                                self.relays[house_alias][relay_name][state["MachineHandle"]]["times"].extend(state["UnixMsList"])
                                self.relays[house_alias][relay_name][state["MachineHandle"]]["values"].extend(state["StateList"])

            for channel in self.data[house_alias]:
                sorted_times_values = sorted(zip(self.data[house_alias][channel]["times"], self.data[house_alias][channel]["values"]))
                sorted_times, sorted_values = zip(*sorted_times_values)
                self.data[house_alias][channel]["times"] = list(sorted_times)
                self.data[house_alias][channel]["values"] = list(sorted_values)

            for relay in self.relays[house_alias]:
                for relay_boss in self.relays[house_alias][relay]:
                    sorted_times_values = sorted(zip(self.relays[house_alias][relay][relay_boss]["times"], 
                                                     self.relays[house_alias][relay][relay_boss]["values"]))
                    sorted_times, sorted_values = zip(*sorted_times_values)
                    self.relays[house_alias][relay][relay_boss]["times"] = list(sorted_times)
                    self.relays[house_alias][relay][relay_boss]["values"] = list(sorted_values)

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
                    self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
                    self.alert_status[house_alias][alert_alias] = True

            elif time.time() - most_recent_ms/1000 > self.max_time_no_data:
                if not self.alert_status[house_alias][alert_alias]:
                    alert_message = f"{house_alias}: No data coming in since {round((time.time()-most_recent_ms/1000)/60,1)} minutes"
                    self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
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
                    print(f"-- {zone} is ok")
                    self.alert_status[house_alias][alert_alias][zone] = False
                else:                    
                    # Check for a recent setpoint increase 
                    setpoint_channel: str = [x for x in channels_by_zone[zone] if "set" in x][0]
                    if len(set(self.data[house_alias][setpoint_channel]["values"])) == 1:
                        if not self.alert_status[house_alias][alert_alias][zone]:
                            alert_message = f"{house_alias}: {setpoint_channel.replace('-set','')} is significantly below setpoint"
                            self.send_opsgenie_alert(alert_message, house_alias, alert_alias+f"_{zone}")
                            self.alert_status[house_alias][alert_alias][zone] = True
                    else:
                        setpoint_values = [x/1000 for x in self.data[house_alias][setpoint_channel]["values"]]
                        if min(setpoint_values) < setpoint_values[-1] and min(setpoint_values)-temperature < self.max_setpoint_violation_f:
                            print(f"-- {zone} is significantly below setpoint but the setpoint was increased recently")
                        else:
                            if not self.alert_status[house_alias][alert_alias][zone]:
                                alert_message = f"{house_alias}: {setpoint_channel.replace('-set','')} is significantly below setpoint"
                                self.send_opsgenie_alert(alert_message, house_alias, alert_alias+f"_{zone}")
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
                or 'dist-pump-pwr' not in self.data[house_alias] or 'dist-flow' not in self.data[house_alias]):
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
            if not power_around_heatcall and pwr['values'][-1] <= self.min_dist_pump_w:
                print(f"- {house_alias}: No pump power recorded around heat call and latest power is low")
                self.alert_status[house_alias][alert_alias] += 1
            elif max(power_around_heatcall) <= self.min_dist_pump_w:
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
                self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
    
    def check_store_pump(self):
        alert_alias = "store_pump"
        print("\nChecking for store pump activity...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = False

            current_relay9_boss = list(self.relays[house_alias]['relay9'].keys())[0]
            latest_relay_time = 0
            for relay9_boss in self.relays[house_alias]['relay9']:
                boss_latest_time = max(self.relays[house_alias]['relay9'][relay9_boss]['times'])
                if boss_latest_time > latest_relay_time:
                    latest_relay_time = boss_latest_time
                    current_relay9_boss = relay9_boss

            r = self.relays[house_alias]['relay9'][current_relay9_boss]
            pairs = list(zip(r["times"], r["values"]))
            time_since_in_current_state = next(
                (pairs[i+1][0] for i in range(len(pairs) - 2, -1, -1) if pairs[i][1] != pairs[i+1][1]),
                pairs[0][0],
            )
            relay9_state = r['values'][-1]

            if 'store-pump-pwr' not in self.data[house_alias] or 'store-flow' not in self.data[house_alias]:
                print(f"{house_alias}: Missing data!") # TODO: create an alert?
                continue

            if relay9_state == "RelayClosed":
                if time.time() - time_since_in_current_state/1000 > 10*60:
                    print(f"- {house_alias}: Relay 9 is closed since more than 10 minutes, expecting store flow")

                    # Try to find power
                    pwr = self.data[house_alias]['store-pump-pwr']
                    power_since_closed = [
                        power for time, power in zip(pwr['times'], pwr['values']) 
                        if time >= time_since_in_current_state
                    ]
                    if not power_since_closed and pwr['values'][-1] <= self.min_store_pump_w:
                        print(f"- {house_alias}: No pump power recorded after relay 9 was closed")
                    elif max(power_since_closed) <= self.min_store_pump_w:
                        print(f"- {house_alias}: No significant pump power after relay 9 was closed")
                    else:
                        print(f"- {house_alias}: Found store pump power after relay 9 was closed")
                        self.alert_status[house_alias][alert_alias] = False
                        continue

                    # Try to find flow
                    flow = self.data[house_alias]['store-flow']
                    flow_since_closed = [
                        flow/100 for time, flow in zip(flow['times'], flow['values']) 
                        if time >= time_since_in_current_state
                    ]
                    if not flow_since_closed and flow['values'][-1] <= self.min_store_pump_gpm:
                        print(f"- {house_alias}: No pump flow recorded after relay 9 was closed")
                    elif max(flow_since_closed) <= self.min_store_pump_gpm:
                        print(f"- {house_alias}: No significant pump flow after relay 9 was closed")
                    else:
                        print(f"- {house_alias}: Found store pump flow after relay 9 was closed")
                        self.alert_status[house_alias][alert_alias] = False
                        continue

                    if not self.alert_status[house_alias][alert_alias]:
                        alert_message = f"{house_alias}: No store pump activity recorded since relay 9 was closed"
                        self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
                        self.alert_status[house_alias][alert_alias] = True
            
            elif relay9_state == "RelayOpen":
                print(f"- {house_alias}: Relay 9 is open, not expecting any store flow at the moment")
                self.alert_status[house_alias][alert_alias] = False

    def check_hp(self):
        alert_alias = "hp_on"
        print("\nChecking for HP activity...")
        for house_alias in self.selected_house_aliases:
            print(f"- {house_alias}:")
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = False

            if 'hp-idu-pwr' not in self.data[house_alias] or 'hp-odu-pwr' not in self.data[house_alias]:
                print(f"{house_alias}: Missing data!") # TODO: create an alert?
                continue

            current_relay5_boss = list(self.relays[house_alias]['relay5'].keys())[0]
            latest_relay_time = 0
            for relay5_boss in self.relays[house_alias]['relay5']:
                boss_latest_time = max(self.relays[house_alias]['relay5'][relay5_boss]['times'])
                if boss_latest_time > latest_relay_time:
                    latest_relay_time = boss_latest_time
                    current_relay5_boss = relay5_boss

            r = self.relays[house_alias]['relay5'][current_relay5_boss]
            pairs = list(zip(r["times"], r["values"]))
            time_since_in_current_state = next(
                (pairs[i+1][0] for i in range(len(pairs) - 2, -1, -1) if pairs[i][1] != pairs[i+1][1]),
                pairs[0][0],
            )
            relay5_state = r['values'][-1]

            if relay5_state == "Scada":
                if time.time() - time_since_in_current_state/1000 > 10*60:
                    print(f"-- Relay 5 is in Scada since more than 10 minutes")
                else:
                    self.alert_status[house_alias][alert_alias] = False
                    print(f"-- The HP should not be on")
                    continue
            else:
                self.alert_status[house_alias][alert_alias] = False
                print(f"-- The HP should not be on")
                continue

            current_relay6_boss = list(self.relays[house_alias]['relay6'].keys())[0]
            latest_relay_time = 0
            for relay6_boss in self.relays[house_alias]['relay6']:
                boss_latest_time = max(self.relays[house_alias]['relay6'][relay6_boss]['times'])
                if boss_latest_time > latest_relay_time:
                    latest_relay_time = boss_latest_time
                    current_relay6_boss = relay6_boss

            r = self.relays[house_alias]['relay6'][current_relay6_boss]
            pairs = list(zip(r["times"], r["values"]))
            time_since_in_current_state = next(
                (pairs[i+1][0] for i in range(len(pairs) - 2, -1, -1) if pairs[i][1] != pairs[i+1][1]),
                pairs[0][0],
            )
            relay6_state = r['values'][-1]

            if relay6_state == "RelayClosed":
                if time.time() - time_since_in_current_state/1000 > 10*60:
                    print(f"-- Relay 6 is Closed since more than 10 minutes")
                else:
                    self.alert_status[house_alias][alert_alias] = False
                    print(f"-- The HP should not be on")
                    continue
            else: 
                self.alert_status[house_alias][alert_alias] = False
                print(f"-- The HP should not be on")
                continue

            print(f"-- The HP should be on")
            odu_channel = self.data[house_alias]['hp-odu-pwr']
            on_times_odu = [t for t, v in zip(odu_channel['times'], odu_channel['values']) if v/1000 >= self.min_hp_kw]
            idu_channel = self.data[house_alias]['hp-idu-pwr']
            on_times_idu = [t for t, v in zip(idu_channel['times'], idu_channel['values']) if v/1000 >= self.min_hp_kw]
            on_times = sorted(on_times_odu + on_times_idu)
            on_times = [x for x in on_times if time.time() - x/1000 < 15*60]
            
            if on_times:
                self.alert_status[house_alias][alert_alias] = False
                print(f"-- The HP is on")
            elif not self.alert_status[house_alias][alert_alias]:
                alert_message = f"{house_alias}: The HP is not coming on"
                self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
                self.alert_status[house_alias][alert_alias] = True
        
    def check_in_atn(self):
        alert_alias = "not_in_atn"
        print("\nChecking that ATN is in control...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = False

            current_relay5_boss = list(self.relays[house_alias]['relay5'].keys())[0]
            latest_relay_time = 0
            for relay9_boss in self.relays[house_alias]['relay5']:
                boss_latest_time = max(self.relays[house_alias]['relay5'][relay9_boss]['times'])
                if boss_latest_time > latest_relay_time:
                    latest_relay_time = boss_latest_time
                    current_relay5_boss = relay9_boss

            if current_relay5_boss == 'a.aa.relay5':
                print(f"- {house_alias}: ATN is in control")
                self.alert_status[house_alias][alert_alias] = False

            elif current_relay5_boss == 'auto.h.n.relay5':
                self.send_opsgenie_alert(f"{house_alias}: Not in Atn!", house_alias, alert_alias)
                self.alert_status[house_alias][alert_alias] = True

    def check_hp_on_during_onpeak(self):
        alert_alias = "hp_onpeak"
        print("\nChecking that the HP is not on during onpeak...")
        for house_alias in self.selected_house_aliases:
            if alert_alias not in self.alert_status[house_alias]:
                self.alert_status[house_alias][alert_alias] = False

            if "hp-odu-pwr" not in self.data[house_alias] or "hp-odu-pwr" not in self.data[house_alias]:
                print(f"{house_alias}: Missing data!") # TODO: create an alert?
                continue

            odu_channel = self.data[house_alias]['hp-odu-pwr']
            on_times_odu = [t for t, v in zip(odu_channel['times'], odu_channel['values']) if v/1000 >= self.min_hp_kw]
            idu_channel = self.data[house_alias]['hp-idu-pwr']
            on_times_idu = [t for t, v in zip(idu_channel['times'], idu_channel['values']) if v/1000 >= self.min_hp_kw]
            on_times = sorted(on_times_odu + on_times_idu)

            sent_alert = False
            for time_ms in on_times:
                time_dt = self.unix_ms_to_date(time_ms)
                if time_dt.hour in self.on_peak_hours and time_dt.day_of_week < 5:
                    if (time_dt.hour == 7 or time_dt.hour == 16) and time_dt.minute == 0:
                        continue
                    if self.alert_status[house_alias][alert_alias]:
                        alert_message = f"{house_alias}: HP was seen on at {time_dt}, which is during onpeak"
                        self.send_opsgenie_alert(alert_message, house_alias, alert_alias)
                        self.alert_status[house_alias][alert_alias] = True
                        sent_alert = True
            
            if not sent_alert:
                print(f"- {house_alias}: HP is not on during onpeak")
                self.alert_status[house_alias][alert_alias] = False

    def main(self):
        while True:
            try:
                self.get_data_from_journaldb()
                self.check_no_data()
                self.check_zone_below_setpoint()
                self.check_dist_pump()
                self.check_store_pump()
                self.check_hp()
                self.check_in_atn()
                self.check_hp_on_during_onpeak()
            except Exception as e:
                print(e)
            time.sleep(self.main_loop_seconds)


if __name__ == '__main__':
    a = AlertGenerator()