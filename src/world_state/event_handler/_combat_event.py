import json
from dataclasses import dataclass

from src.settings import Consts

@dataclass(slots=True)
class CombatEvent:
    event_id: int = Consts.EMPTY_EVENT_ID

    timestamp: int = Consts.EMPTY_TIMESTAMP
    source_id: int = Consts.EMPTY_OBJ_ID
    spell_id: int = Consts.EMPTY_SPELL_ID
    target_id: int = Consts.EMPTY_OBJ_ID

    validation_error_msg: str = ""

    @classmethod
    def deserialize(cls, data: str) -> 'CombatEvent':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            event_id=d["event_id"],
            timestamp=d["timestamp"],
            source_id=d["source_id"],
            spell_id=d["spell_id"],
            target_id=d["target_id"],
            validation_error_msg=d.get("error_msg"),
        )

    def serialize(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source_id": self.source_id,
            "spell_id": self.spell_id,
            "target_id": self.target_id,
            "error_msg": self.validation_error_msg,
        })

    @property
    def outcome_is_successful(self) -> bool:
        return self.validation_error_msg == ""

    @property
    def combat_data(self) -> tuple[int, int, int, int]:
        return self.timestamp, self.source_id, self.spell_id, self.target_id
