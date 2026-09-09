from dataclasses import dataclass
from typing import Dict

@dataclass(slots=True)
class ObjVisualsData:
    color_red: int
    color_green: int
    color_blue: int
    sprite_name: str

    @classmethod
    def create_environment(cls) -> "ObjVisualsData":
        return cls(255, 255, 255, "")

    @classmethod
    def create_spawned(cls) -> "ObjVisualsData":
        return cls(255, 255, 255, "")

class VisualsSystem:
    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjVisualsData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_environment()

    def spawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_spawned()

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    # ---- State Update Handlers ----

    def get_obj_visuals(self, obj_id: int) -> ObjVisualsData:
        return self.game_obj_data_dct[obj_id]

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if effect_type == "color_red":
            if data := self.game_obj_data_dct.get(source_id): data.color_red = int(effect_value)
        elif effect_type == "color_green":
            if data := self.game_obj_data_dct.get(source_id): data.color_green = int(effect_value)
        elif effect_type == "color_blue":
            if data := self.game_obj_data_dct.get(source_id): data.color_blue = int(effect_value)

    def apply_cosmetic(self, cosmetic_type: str, cosmetic_value: str, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        if cosmetic_type == "sprite_name":
            if data := self.game_obj_data_dct.get(source_id):
                data.sprite_name = cosmetic_value