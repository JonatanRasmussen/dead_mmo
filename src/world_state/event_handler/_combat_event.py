import json
from dataclasses import dataclass

from src.settings import Consts

@dataclass(slots=True)
class CombatEvent:
    event_id: int = Consts.EMPTY_ID

    timestamp: int = Consts.EMPTY_TIMESTAMP
    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    validation_error_msg: str = ""

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
            validation_error_msg=d.get("err"),
            spell_modifier=d["sm"],
        )

    def serialize(self) -> str:
        return json.dumps({
            "eid": self.event_id,
            "ts": self.timestamp,
            "sid": self.source_id,
            "sp": self.spell_id,
            "tid": self.target_id,
            "err": self.validation_error_msg,
            "sm": self.spell_modifier,
        })

    @property
    def outcome_is_successful(self) -> bool:
        return self.validation_error_msg == ""