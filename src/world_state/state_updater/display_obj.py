from dataclasses import dataclass
from src.settings import Consts

@dataclass(slots=True)
class DisplayObj:
    obj_id: int = Consts.EMPTY_OBJ_ID
    hitbox_xy: tuple[float, float] = (0.0, 0.0)
    offset_xy: tuple[float, float] = (0.0, 0.0)
    is_visible: bool = False
    draw_as_square: bool = False
    height: float = 64.0
    width: float = 64.0
    color_rgb: tuple[int, int, int] = (0, 0, 0)
    sprite_id: int = Consts.EMPTY_ASSET_ID
    sprite_name: str = Consts.EMPTY_ASSET_NAME
    sprite_index: int = 0
    sprite_scale: float = 1.0
    audio_id: int = Consts.EMPTY_ASSET_ID
    audio_name: str = Consts.EMPTY_ASSET_NAME
    audio_start: int = Consts.EMPTY_TIMESTAMP
    audio_loop: bool = False

    @property
    def pos_xy(self) -> tuple[float, float]:
        return self.hitbox_xy[0] + self.offset_xy[0], self.hitbox_xy[1] + self.offset_xy[1]

    @property
    def has_sprite(self) -> bool:
        return self.sprite_id != Consts.EMPTY_ASSET_ID and self.sprite_index != 0

    @property
    def diameter(self) -> float:
        return min(self.height, self.width)

    @property
    def obj_scale_xy(self) -> tuple[float, float]:
        if self.sprite_id != Consts.EMPTY_ASSET_ID:
            return self.width * self.sprite_scale, self.height * self.sprite_scale
        return self.width, self.height

    @property
    def obj_diameter(self) -> float:
        if self.sprite_id != Consts.EMPTY_ASSET_ID:
            return self.diameter * self.sprite_scale
        return self.diameter

    @property
    def sprite_asset_name(self) -> str:
        if not self.has_sprite:
            return ""
        return str(self.sprite_name) + "_" + str(self.sprite_index)