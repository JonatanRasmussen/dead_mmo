from typing import Iterable, ValuesView
from enum import Enum, auto
from src.settings import Consts
from .default_ids import DefaultIDs
from src.models.components import GameObj


class Targeting(Enum):
    """ Defines targeting behavior for spell """
    NONE = 0
    SELF = auto()
    TARGET = auto()
    TARGET_OF_TARGET = auto()
    PARENT = auto()
    TARGET_OF_PARENT = auto()
    DEFAULT_FRIENDLY = auto()
    DEFAULT_ENEMY = auto()
    TAB_TO_NEXT = auto()