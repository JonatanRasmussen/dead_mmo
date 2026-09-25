from abc import ABC, abstractmethod
from .display_obj import DisplayObj

class System(ABC):

    @abstractmethod
    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        ...

    @abstractmethod
    def get_effect_types(self) -> set[str]:
        ...

    @abstractmethod
    def get_validation_types(self) -> set[str]:
        ...

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