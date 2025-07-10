from dataclasses import dataclass

from src.config import Colors

@dataclass(slots=True)
class Visuals:
    """ Cooldowns, cast timers and other things happening over time. """
    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE
    sprite_name: str = ""
    audio_name: str = ""