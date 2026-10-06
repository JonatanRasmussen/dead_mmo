from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .system_interface import DisplayObj, GameObj, System

class SfxEffect(str, Enum):
    START_PLAY_AUDIO = "play_audio"

class SfxValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjSfxData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    audio_id: int = Consts.EMPTY_ASSET_ID
    audio_start: int = Consts.EMPTY_TIMESTAMP

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjSfxData":
        return cls(obj_id=game_obj.obj_id)


class SfxSystem(System):

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._data_dct: dict[int, ObjSfxData] = {}

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.audio_id = float(data.audio_id)
            display_obj.audio_start = data.audio_start
        return display_obj

    def get_effect_types(self) -> set[str]:
        return {e.value for e in SfxEffect}

    def get_validation_types(self) -> set[str]:
        return {v.value for v in SfxValidation}

    def spawn_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"Error: GameObj {game_obj.obj_id} already exist."
        self._game_objs[game_obj.obj_id] = game_obj

    def get_data(self, obj_id: int) -> ObjSfxData:
        if obj_id in self._data_dct:
            return self._data_dct[obj_id]
        assert obj_id in self._game_objs, f"Error: GameObj {obj_id} does not exist."
        game_obj = self._game_objs[obj_id]
        data = ObjSfxData.create_from_game_obj(game_obj)
        self._data_dct[obj_id] = data
        return data

    def remove_data(self, obj_id: int) -> None:
        self.get_data(obj_id)  # Assert that data exists
        self._data_dct.pop(obj_id, None)


    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        match effect_type:
            case SfxEffect.START_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_id = int(effect_value)
                data.audio_start = timestamp
                return Consts.EMPTY_SPELL_ID
            case _:
                return Consts.EMPTY_SPELL_ID