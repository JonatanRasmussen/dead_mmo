from dataclasses import dataclass
import json

from src.settings import Consts
from .faction import Faction

@dataclass(slots=True)
class Resources:
    """ Resources used by GameObjs such as health, mana and spell charges. """
    hp: float = 0.0
    team: Faction = Faction.EMPTY

    @classmethod
    def deserialize(cls, data: str) -> 'Resources':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            hp=d["hp"],
            team=Faction(d["tm"])
        )
    def serialize(self) -> str:
        return json.dumps({
            "hp": self.hp,
            "tm": self.team.value
        })