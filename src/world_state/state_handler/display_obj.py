from dataclasses import dataclass
from src.settings import Consts

@dataclass(slots=True)
class DisplayObj:
    obj_id: int = Consts.EMPTY_OBJ_ID
    pos_xy: tuple[float, float] = (0.0, 0.0)
    is_visible: bool = False
    size: float = 0.0
    color_rgb: tuple[int, int, int] = (0, 0, 0)
    sprite_id: float = float(Consts.EMPTY_ASSET_ID)
    sprite_name: str = Consts.EMPTY_ASSET_NAME
    sprite_index: int = 0
    sprite_scale: float = 0.0
    audio_id: float = float(Consts.EMPTY_ASSET_ID)
    audio_name: str = Consts.EMPTY_ASSET_NAME
    audio_start: int = Consts.EMPTY_TIMESTAMP

    @property
    def has_sprite(self) -> bool:
        return self.sprite_id != Consts.EMPTY_ASSET_ID and self.sprite_index != 0

    @property
    def obj_scale(self) -> float:
        if self.sprite_id != 0.0:
            return self.sprite_scale
        return self.size

    @property
    def sprite_asset_name(self) -> str:
        if not self.has_sprite:
            return ""
        return str(self.sprite_name)+"_"+str(self.sprite_index)