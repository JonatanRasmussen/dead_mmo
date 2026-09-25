from dataclasses import dataclass
from src.settings import Consts


@dataclass(slots=True)
class DisplayObj:
    obj_id: int = Consts.EMPTY_ID
    pos_xy: tuple[float, float] = (0.0, 0.0)
    is_visible: bool = False
    size: float = 0.0
    color_rgb: tuple[int, int, int] = (0, 0, 0)
    sprite_id: float = float(Consts.EMPTY_ID)
    sprite_name: str = Consts.EMPTY_ASSET_NAME
    audio_id: float = float(Consts.EMPTY_ID)
    audio_name: str = Consts.EMPTY_ASSET_NAME
    audio_start: int = Consts.EMPTY_TIMESTAMP
