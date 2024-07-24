import bisect
from typing import List
from typing import Tuple


class AliasMapper:
    def __init__(self, scada: str):
        self.scada = scada
        self.channel_mappings = {}

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
