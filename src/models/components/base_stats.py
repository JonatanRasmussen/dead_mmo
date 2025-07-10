from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class BaseStats:
    """ Multiplicative values for GameObjs such as stats, weights and other modifiers """
    movement_speed: float = 1.0