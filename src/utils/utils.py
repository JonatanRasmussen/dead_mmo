from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, ValuesView, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
import math
import json
from src.model.models import IdGen, SpellFlag, Spell, Aura, PlayerInput, EventTrigger, EventOutcome, CombatEvent, GameObjStatus, GameObj

class Utils:
    @staticmethod
    def load_collection(class_with_methods: Type[Any]) -> List[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]

    @staticmethod
    def create_player_input_dct(list_of_inputs: List[PlayerInput]) -> Dict[float, PlayerInput]:
        inputs_dct: SortedDict[float, PlayerInput] = SortedDict()
        for player_input in list_of_inputs:
            inputs_dct[player_input.local_timestamp] = player_input
        return inputs_dct
