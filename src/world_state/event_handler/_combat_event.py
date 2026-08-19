import json
from dataclasses import dataclass

from src.settings import Consts
from ._outcome import Outcome

@dataclass(slots=True)
class CombatEvent:
    event_id: int = Consts.EMPTY_ID

    timestamp: int = Consts.EMPTY_TIMESTAMP
    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    outcome: Outcome = Outcome.EMPTY

    spell_modifier: float = 1.0

    @classmethod
    def deserialize(cls, data: str) -> 'CombatEvent':
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
        return self.outcome.outcome_is_valid