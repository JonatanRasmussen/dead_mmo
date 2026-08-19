import copy
import json
from typing import Iterable, Optional
from dataclasses import dataclass, field
from enum import IntFlag, Enum, auto

from src.settings import Consts

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
    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    outcome: Outcome = Outcome.EMPTY

    spell_modifier: float = 1.0

    @classmethod
    def deserialize(cls, data: str) -> 'UpcomingEvent':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            event_id=d["eid"],
            timestamp=d["ts"],
            source_id=d["sid"],
            spell_id=d["sp"],
            target_id=d["tid"],
            spell_modifier=d["sm"],
        )

    def serialize(self) -> str:
        return json.dumps({
            "eid": self.event_id,
            "ts": self.timestamp,
            "sid": self.source_id,
            "sp": self.spell_id,
            "tid": self.target_id,
            "sm": self.spell_modifier,
        })

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome.is_success

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] {self.outcome} (obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.target_id:04d}.)"

    @property
    def key(self) -> tuple[int, int]:
        return (self.timestamp, self.event_id)

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    def finalize_event(self, target_id: int, outcome: Outcome) -> 'UpcomingEvent':
        return UpcomingEvent(
            event_id=self.event_id,
            timestamp=self.timestamp,
            source_id=self.source_id,
            spell_id=self.spell_id,
            target_id = target_id,
            outcome = outcome,
        )

