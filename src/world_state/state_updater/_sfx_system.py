from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj

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


class SfxSystem(BaseSystem):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjSfxData, SfxEffect, SfxValidation)

    def get_data(self, obj_id: int) -> ObjSfxData:
        return super().get_data(obj_id)

    def build_display_obj(self, current_time: int, obj_id: int, display_obj: DisplayObj) -> DisplayObj:
        if obj_id in self._data_dct:
            data = self.get_data(obj_id)
            display_obj.audio_id = float(data.audio_id)
            display_obj.audio_start = data.audio_start
        return display_obj

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case SfxEffect.START_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_id = int(effect_value)
                data.audio_start = timestamp
        return triggered_spell_id