from dataclasses import dataclass

from src.settings import Consts
from .faction import Faction

@dataclass(slots=True)
class Resources:
    """ Resources used by GameObjs such as health, mana and spell charges. """
    hp: float = 0.0
    team: Faction = Faction.EMPTY