from typing import Tuple, NamedTuple, Optional
from enum import Enum, auto

from src.config import Consts


class UpcomingEvent(NamedTuple):
    timestamp: float = Consts.EMPTY_TIMESTAMP
    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    priority: int = 0

    aura_origin_spell_id: int = Consts.EMPTY_ID
    aura_id: int = Consts.EMPTY_ID

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    @property
    def is_aura_tick(self) -> bool:
        return Consts.is_valid_id(self.aura_origin_spell_id)

    def update_source_and_target(self, new_source_id: int, new_target_id: int) -> 'UpcomingEvent':
        return self._replace(source_id=new_source_id, target_id=new_target_id)

    def continue_spell_sequence(self, new_spell_id: int) -> 'UpcomingEvent':
        return self._replace(spell_id=new_spell_id)

    def also_target(self, new_spell_id: int, new_target_id: int) -> 'UpcomingEvent':
        return self._replace(spell_id=new_spell_id, target_id=new_target_id)

