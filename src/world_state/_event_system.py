from typing import Iterable
from dataclasses import dataclass
import json
from enum import Enum, auto

from src.settings import Consts
from src.utils.copy_utils import CopyTools


class Outcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()
    AURA_NO_LONGER_EXISTS = auto()

    @property
    def is_success(self) -> bool:
        return self in {Outcome.SUCCESS}


@dataclass(slots=True)
class UpcomingEvent:
    event_id: int = Consts.EMPTY_ID
    timestamp: int = Consts.EMPTY_TIMESTAMP
    priority: int = 0

    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    outcome: Outcome = Outcome.EMPTY

    spell_modifier: float = 1.0

    aura_id: int = Consts.EMPTY_ID
    aura_origin_spell_id: int = Consts.EMPTY_ID
    #aura_start_time: int = Consts.EMPTY_TIMESTAMP
    is_spell_sequence: bool = False
    is_aoe_targeting: bool = False

    @classmethod
    def deserialize(cls, data: str) -> 'UpcomingEvent':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            event_id=d["eid"],
            timestamp=d["ts"],
            priority=d["pr"],
            source_id=d["sid"],
            spell_id=d["sp"],
            target_id=d["tid"],
            spell_modifier=d["sm"],
            aura_id=d["aid"],
            aura_origin_spell_id=d["aos"],
            is_spell_sequence=d["seq"],
            is_aoe_targeting=d["aoe"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "eid": self.event_id,
            "ts": self.timestamp,
            "pr": self.priority,
            "sid": self.source_id,
            "sp": self.spell_id,
            "tid": self.target_id,
            "sm": self.spell_modifier,
            "aid": self.aura_id,
            "aos": self.aura_origin_spell_id,
            "seq": self.is_spell_sequence,
            "aoe": self.is_aoe_targeting
        })

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome.is_success

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] {self.outcome} (obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.target_id:04d}.)"

    @property
    def key(self) -> tuple[int, int, int, int, int]:
        return (self.timestamp, self.priority, self.source_id, self.target_id, self.spell_id)

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    @property
    def is_aura_tick(self) -> bool:
        return Consts.is_valid_id(self.aura_origin_spell_id)

    def finalize_event(self, source_id: int, target_id: int, outcome: Outcome) -> 'UpcomingEvent':
        f_event = self.create_copy()
        f_event.source_id = source_id
        f_event.target_id = target_id
        f_event.outcome = outcome
        return f_event

    def create_copy(self) -> 'UpcomingEvent':
        return CopyTools.full_copy(self)
