from dataclasses import dataclass
from typing import Dict
from src.world_state.state_handler._spell_loader import Effect

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
    def create_spawned(cls, r: int, g: int, b: int, sprite: str) -> "ObjVisualsData":
        return cls(r, g, b, sprite)

class VisualsSystem:
    def __init__(self) -> None:
        self.game_obj_data_dct: Dict[int, ObjVisualsData] = {}

    def create_environment_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_environment()

    def spawn_game_obj(self, obj_id: int, r: int, g: int, b: int, sprite: str) -> None:
        self.game_obj_data_dct[obj_id] = ObjVisualsData.create_spawned(r, g, b, sprite)

    def despawn_game_obj(self, obj_id: int) -> None:
        self.game_obj_data_dct.pop(obj_id, None)

    # ---- State Update Handlers ----

    def change_color_rgb(self, source_id: int, r: int, g: int, b: int) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.color_red, data.color_green, data.color_blue = r, g, b

    def change_sprite(self, source_id: int, sprite_name: str) -> None:
        if data := self.game_obj_data_dct.get(source_id):
            data.sprite_name = sprite_name

    def get_obj_visuals(self, obj_id: int) -> ObjVisualsData:
        return self.game_obj_data_dct[obj_id]

    def apply_effect(self, effect: Effect, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        # Implemented for completeness so StateHandler can blindly invoke this method in its loop
        pass