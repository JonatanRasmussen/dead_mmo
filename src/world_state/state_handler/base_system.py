from abc import ABC, abstractmethod
from typing import Any, Type
from enum import Enum
from .display_obj import DisplayObj
from .game_obj import GameObj


class BaseSystem(ABC):
    def __init__(self, game_objs: dict[int, GameObj], data_class: Type, effect_enum: Type[Enum], validation_enum: Type[Enum]):
        # Reference to the authoritative dictionary owned by StateHandler
        self._game_objs = game_objs
        self._data_dct: dict[int, Any] = {}

        self._data_class = data_class
        self._effect_enum = effect_enum
        self._validation_enum = validation_enum

    def get_effect_types(self) -> set[str]:
        return {e.value for e in self._effect_enum}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in self._validation_enum}

    def get_data(self, obj_id: int) -> Any:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]

        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."

        # Lazy-load the data using the classmethod you already have on all your dataclasses
        data = self._data_class.create_from_game_obj(self._game_objs[obj_id])
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        # We only pop from our specific data dictionary.
        # StateHandler is responsible for removing the base GameObj from self._game_objs!
        self._data_dct.pop(obj_id, None)

    # --- Abstract Methods that individual systems MUST implement ---

    @abstractmethod
    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        ...

    @abstractmethod
    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        ...

    @abstractmethod
    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        ...