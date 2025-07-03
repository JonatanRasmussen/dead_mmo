from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class DefaultIDs:
    environment_id: int = Consts.EMPTY_ID
    player_id: int = Consts.EMPTY_ID
    boss1_id: int = Consts.EMPTY_ID
    boss2_id: int = Consts.EMPTY_ID

    @property
    def missing_target_id(self) -> int:
        return self.environment_id
    @property
    def default_allied_id(self) -> int:
        if self.player_exists:
            return self.player_id
        return self.missing_target_id
    @property
    def default_hostile_id(self) -> int:
        if self.boss1_exists:
            return self.boss1_id
        return self.missing_target_id

    @property
    def environment_exists(self) -> bool:
        return Consts.is_valid_id(self.environment_id)
    @property
    def player_exists(self) -> bool:
        return Consts.is_valid_id(self.player_id)
    @property
    def boss1_exists(self) -> bool:
        return Consts.is_valid_id(self.boss1_id)
    @property
    def boss2_exists(self) -> bool:
        return Consts.is_valid_id(self.boss2_id)

