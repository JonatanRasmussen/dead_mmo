from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class Waitouts:
    """ Cooldowns, cast timers and other things happening over time. """
    spawn_timestamp: int = Consts.EMPTY_TIMESTAMP
    gcd_start: int = Consts.EMPTY_TIMESTAMP
    ability_1_cd_start: int = Consts.EMPTY_TIMESTAMP
    ability_2_cd_start: int = Consts.EMPTY_TIMESTAMP
    ability_3_cd_start: int = Consts.EMPTY_TIMESTAMP
    ability_4_cd_start: int = Consts.EMPTY_TIMESTAMP

    def get_time_since_spawn(self, current_time: int) -> int:
        return current_time - self.spawn_timestamp
