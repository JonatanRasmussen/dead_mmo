from dataclasses import dataclass, asdict, field
from sortedcontainers import SortedDict  # type: ignore
from typing import Any, Dict, List, Tuple, Type, Optional, FrozenSet, Literal, Final, TypedDict, ClassVar, Set, Deque, NamedTuple
from collections import deque
from enum import Enum, Flag, auto
from types import MappingProxyType
from copy import copy, deepcopy
from src.config.color import Color
from src.config.consts import Consts


class IdGen:
    """ ID generator that provides unique IDs from a set of assigned integers. """
    EMPTY_ID = Consts.EMPTY_ID

    def __init__(self) -> None:
        self._reserved_ids: Set[int] = set({IdGen.EMPTY_ID})
        self._assigned_ids: Deque[int] = deque()

    @classmethod
    def create_preassigned_range(cls, id_start: int, id_stop: int) -> 'IdGen':
        id_gen = IdGen()
        id_gen.assign_id_range(id_start, id_stop)
        return id_gen

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == IdGen.EMPTY_ID

    @staticmethod
    def is_valid_id(id_num: int) -> bool:
        return not IdGen.is_empty_id(id_num)

    def assign_id_range(self, start: int, stop: int) -> None:
        for id_num in range(start, stop):
            if id_num not in self._reserved_ids:
                self._assigned_ids.append(id_num)

    def generate_new_id(self) -> int:
        if not self._assigned_ids:
            assert self._assigned_ids, "No more IDs available."
            return IdGen.EMPTY_ID
        return self._assigned_ids.popleft()

    def reserve_id(self, reserved_id: int) -> None:
        self._reserved_ids.add(reserved_id)
        self._assigned_ids = deque(id_num for id_num in self._assigned_ids if id_num != reserved_id)


