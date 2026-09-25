from dataclasses import dataclass
from enum import Enum
from src.settings import Consts
from .system_interface import System, DisplayObj


class DisplayEffect(str, Enum):
    APPLY_COLOR_RED = "color_red"
    APPLY_COLOR_GREEN = "color_green"
    APPLY_COLOR_BLUE = "color_blue"
    APPLY_ICON_ID = "icon_id"
    TURN_INVISIBLE = "turn_invisible"
    START_PLAY_AUDIO = "play_audio"


class DisplayValidation(str, Enum):
    pass


@dataclass(slots=True)
class ObjDisplayData:
    obj_id: int = Consts.EMPTY_ID
    color_red: int = 255
    color_green: int = 255
    color_blue: int = 255
    color_alpha: float = 1.0
    icon_id: int = Consts.EMPTY_ID
    is_visible: bool = True
    audio_id: int = Consts.EMPTY_ID
    audio_start: int = -1

    @classmethod
    def create_new_obj(cls, new_obj_id: int) -> "ObjDisplayData":
        return cls(
            obj_id=new_obj_id,
        )


class DisplaySystem(System):

    def __init__(self) -> None:
        self._data_dct: dict[int, ObjDisplayData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        data = self.get_data(obj_id)
        display_obj.is_visible = data.is_visible
        display_obj.color_rgb = (data.color_red, data.color_green, data.color_blue)
        display_obj.sprite_id = data.icon_id
        display_obj.audio_id = data.audio_id
        display_obj.audio_start = data.audio_start
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in DisplayEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in DisplayValidation}

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, parent_id: int, spell_id: int, target_id: int) -> None:
        game_obj = ObjDisplayData.create_new_obj(new_obj_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjDisplayData(obj_id=obj_id, is_visible=False)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjDisplayData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjDisplayData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)

    # ---- State Lookups ----

    def is_visible(self, obj_id: int) -> bool:
        return self._data_dct.get(obj_id, ObjDisplayData()).is_visible

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, target_id: int) -> None:
        if effect_type == DisplayEffect.APPLY_COLOR_RED:
            self.get_data(target_id).color_red = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_COLOR_GREEN:
            self.get_data(target_id).color_green = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_COLOR_BLUE:
            self.get_data(target_id).color_blue = int(effect_value)
        elif effect_type == DisplayEffect.APPLY_ICON_ID:
            self.get_data(target_id).icon_id = int(effect_value)
        elif effect_type == DisplayEffect.TURN_INVISIBLE:
            self.get_data(target_id).is_visible = False
        elif effect_type == DisplayEffect.START_PLAY_AUDIO:
            data = self.get_data(target_id)
            data.audio_id = int(effect_value)
            data.audio_start = timestamp