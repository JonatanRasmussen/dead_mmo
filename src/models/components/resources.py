from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class Resources:
    """ Resources used by GameObjs such as health, mana and spell charges. """
    hp: float = 0.0