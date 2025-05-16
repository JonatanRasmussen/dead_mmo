from typing import NamedTuple, List
from enum import Enum

from src.handlers.id_gen import IdGen
from src.models.game_obj import GameObj
from src.models.spell import Spell

class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = 1
    FAILED = 2
    MISSED = 3


class CombatEvent(NamedTuple):
    event_id: int = IdGen.EMPTY_ID
    base_event: int = IdGen.EMPTY_ID
    timestamp: float = 0.0
    source: int = IdGen.EMPTY_ID
    spell: int = IdGen.EMPTY_ID
    target: int = IdGen.EMPTY_ID
    is_periodic_tick: bool = False

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] (obj_{self.source:04d} uses spell_{self.spell:04d} on obj_{self.target:04d}.)"

    @property
    def is_subevent(self) -> bool:
        return not IdGen.is_empty_id(self.base_event)

    @property
    def has_target(self) -> bool:
        return not IdGen.is_empty_id(self.target)

    def update_target(self, new_target: int) -> 'CombatEvent':
        return self._replace(target=new_target)

    def continue_spell_sequence(self, new_event_id: int, new_spell_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, base_event=self.event_id, spell=new_spell_id)

    def also_target(self, new_event_id: int, new_target_id: int) -> 'CombatEvent':
        return self._replace(event_id=new_event_id, target=new_target_id)


class FinalizedEvent(NamedTuple):
    combat_event: CombatEvent = CombatEvent()
    source: GameObj = GameObj()
    spell: Spell = Spell()
    target: GameObj = GameObj()
    outcome: EventOutcome = EventOutcome.EMPTY

    @property
    def timestamp(self) -> float:
        return self.combat_event.timestamp

    @property
    def source_id(self) -> int:
        return self.source.obj_id

    @property
    def spell_id(self) -> int:
        return self.spell.spell_id

    @property
    def target_id(self) -> int:
        return self.target.obj_id

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome != EventOutcome.FAILED

    @property
    def is_aura(self) -> bool:
        return self.spell.is_aura
