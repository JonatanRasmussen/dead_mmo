from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class BaseStats:
    """ Multiplicative values for GameObjs such as stats, weights and other modifiers """
    base_size: float = 1.0
    movement_speed: float = 1.0