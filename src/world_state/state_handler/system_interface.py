from abc import ABC, abstractmethod


class System(ABC):
    @abstractmethod
    def spawn_game_obj(self, timestamp: int, new_obj_id: int, parent_id: int, spell_id: int, target_id: int) -> None:
        ...

    @abstractmethod
    def spawn_environment_obj(self, obj_id: int) -> None:
        ...

    @abstractmethod
    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        ...

    @abstractmethod
    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, target_id: int) -> None:
        ...