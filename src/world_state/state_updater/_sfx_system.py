from dataclasses import dataclass
from enum import Enum

from src.settings import Consts
from .base_system import BaseSystem, DisplayObj, GameObj

class SfxEffect(str, Enum):
    START_PLAY_AUDIO = "play_audio"
    STOP_PLAY_AUDIO = "stop_audio"
    LOOP_AUDIO = "loop_audio"

class SfxValidation(str, Enum):
    pass

@dataclass(slots=True)
class ObjSfxData:
    obj_id: int = Consts.EMPTY_OBJ_ID
    audio_id: int = Consts.EMPTY_ASSET_ID
    audio_start: int = Consts.EMPTY_TIMESTAMP
    loop_audio: bool = False

    @classmethod
    def create_from_game_obj(cls, game_obj: GameObj) -> "ObjSfxData":
        return cls(obj_id=game_obj.obj_id)


class SfxSystem(BaseSystem[ObjSfxData]):

    def __init__(self, game_objs: dict[int, GameObj]) -> None:
        super().__init__(game_objs, ObjSfxData, SfxEffect, SfxValidation)

    def validate_event(self, validation_type: str, validation_value: int, timestamp: int, source_id: int, dest_id: int) -> bool:
        match validation_type:
            case _:
                return True

    def apply_effect(self, effect_type: str, effect_value: int, timestamp: int, obj_id: int) -> int:
        triggered_spell_id = Consts.EMPTY_SPELL_ID
        match effect_type:
            case SfxEffect.START_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_id = effect_value
                data.audio_start = timestamp
            case SfxEffect.STOP_PLAY_AUDIO:
                data = self.get_data(obj_id)
                data.audio_start = Consts.EMPTY_TIMESTAMP
            case SfxEffect.LOOP_AUDIO:
                data = self.get_data(obj_id)
                data.loop_audio = bool(effect_value)
        return triggered_spell_id