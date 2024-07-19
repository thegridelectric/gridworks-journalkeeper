import bisect
from typing import List
from typing import Tuple

from gwp.first_season.beech_channels import BeechChannels as BC


class BeechAliasMapper:
    def __init__(self, scada: str = "beech"):
        self.scada = scada
        self.channel_mappings = {
            BC.ELT1_PWR: [
                (1699886100, "a.elt1"),  # 2023-11-13 09:35 America/NY
            ],
            BC.DIST_FLOW_INTEGRATED: [
                (1699886100, "a.dist.flow"),  # 2023-11-13 09:35 America/NY
            ],
            BC.DIST_SWT: [
                (1699886100, "a.dist.swt.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.DIST_RWT: [
                (1699886100, "a.dist.rwt.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.HP_EWT: [
                (1699886100, "a.hp.ewt.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.HP_FOSSIL_LWT: [
                (1699886100, "a.hp.fossil.lwt.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.HP_LWT: [
                (1699886100, "a.hp.lwt.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.PRIMARY_FLOW_INTEGRATED: [
                (1699886100, "a.primary.flow"),  # 2023-11-13 09:35 America/NY
            ],
            BC.OAT: [
                (1699886100, "a.outdoor.air.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.STORE_COLD_PIPE_TEMP: [
                (1699886100, "a.buffer.cold.pipe.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.STORE_FLOW_INTEGRATED: [
                (1699886100, "a.store.flow"),  # 2023-11-13 09:35 America/NY
            ],
            BC.STORE_HOT_PIPE_TEMP: [
                (1699886100, "a.buffer.hot.pipe.temp"),  # 2023-11-13 09:35 America/NY
            ],
            BC.TANK1_DEPTH1: [
                (1699886100, "a.tank1.temp.depth1"),  # 2023-11-13 09:35 America/NY
            ],
            BC.TANK1_DEPTH2: [
                (1699886100, "a.tank1.temp.depth2"),  # 2023-11-13 09:35 America/NY
            ],
            BC.TANK1_DEPTH3: [
                (1699886100, "a.tank1.temp.depth3"),  # 2023-11-13 09:35 America/NY
            ],
            BC.TANK1_DEPTH4: [
                (1699886100, "a.tank1.temp.depth4"),  # 2023-11-13 09:35 America/NY
            ],
        }

    def add_name_mapping(self, name: str, mappings: List[Tuple[int, str]]):
        self.channel_mappings[name] = mappings

    def lookup_name(self, alias: str, timestamp: int) -> str:
        for name, mappings in self.channel_mappings.items():
            # Extract the timestamps and aliases
            timestamps = [entry[0] for entry in mappings]
            aliases = [entry[1] for entry in mappings]

            # Find the right index using binary search
            index = bisect.bisect_right(timestamps, timestamp) - 1

            if index >= 0 and aliases[index] == alias:
                return name

        raise ValueError(
            f"No valid mapping found for alias '{alias}' at timestamp {timestamp}."
        )
