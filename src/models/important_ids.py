from typing import NamedTuple
from src.handlers.id_gen import IdGen


class ImportantIDs(NamedTuple):
    setup_spell_id: int = IdGen.EMPTY_ID
    environment_id: int = IdGen.EMPTY_ID
    player_id: int = IdGen.EMPTY_ID
    boss1_id: int = IdGen.EMPTY_ID
    boss2_id: int = IdGen.EMPTY_ID

    @property
    def missing_target_id(self) -> int:
        return self.environment_id
    @property
    def setup_spell_exists(self) -> bool:
        return IdGen.is_valid_id(self.setup_spell_id)
    @property
    def environment_exists(self) -> bool:
        return IdGen.is_valid_id(self.environment_id)
    @property
    def player_exists(self) -> bool:
        return IdGen.is_valid_id(self.player_id)
    @property
    def boss1_exists(self) -> bool:
        return IdGen.is_valid_id(self.boss1_id)
    @property
    def boss2_exists(self) -> bool:
        return IdGen.is_valid_id(self.boss2_id)

    def initialize_environment(self, setup_spell_id: int, environment_id: int) -> 'ImportantIDs':
        return self._replace(setup_spell_id=setup_spell_id, environment_id=environment_id)

    def update_player_id(self, new_player_id: int) -> 'ImportantIDs':
        return self._replace(player_id=new_player_id)

    def update_boss1_id(self, new_boss1_id: int) -> 'ImportantIDs':
        return self._replace(boss1_id=new_boss1_id)

    def update_boss2_id(self, new_boss2_id: int) -> 'ImportantIDs':
        return self._replace(boss2_id=new_boss2_id)
