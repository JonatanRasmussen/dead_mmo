from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Generic, Protocol
from enum import Enum
from .display_obj import DisplayObj
from .game_obj import GameObj


class SystemDataProtocol(Protocol):
    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> Any: ...
    def __init__(self) -> None: ...


T = TypeVar('T', bound=SystemDataProtocol)


class BaseSystem(ABC, Generic[T]):
    def __init__(self, game_objs: dict[int, GameObj], data_class: Type[T], effect_enum: Type[Enum], validation_enum: Type[Enum]):
        # Reference to the authoritative dictionary owned by StateHandler
        self._game_objs = game_objs
        self._data_dct: dict[int, T] = {}

        self._data_class = data_class
        self._effect_enum = effect_enum
        self._validation_enum = validation_enum

    def get_effect_types(self) -> set[str]:
        return {e.value for e in self._effect_enum}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in self._validation_enum}

    def get_data(self, obj_id: int) -> T:
        """Gets the data for an object, lazy-initializing it if it doesn't exist."""
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        data = self._data_class.create_from_game_obj(self._game_objs[obj_id])
        self._data_dct[obj_id] = data
        return data

    def get_read_only_data(self, obj_id: int) -> T:
        """
        Returns the data for the object if it exists.
        If not, returns a temporary default instance WITHOUT saving it to the dictionary.
        Use this for rendering and read-only queries to prevent lazy-init side effects.
        """
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        if obj_id in self._game_objs:
            return self._data_class.create_from_game_obj(self._game_objs[obj_id])
        print(f"Error: {obj_id} does not exist. This should be impossible.")
        return self._data_class()

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id, None)

    # --- Abstract Methods that individual systems MUST implement ---

    @abstractmethod
    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        ...

    @abstractmethod
    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        ...