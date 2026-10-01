import pygame
from typing import Any, Optional
from pathlib import Path
from dataclasses import dataclass
from PIL import Image, ImageSequence

@dataclass
class Animation:
    frames: list[pygame.Surface]
    frame_duration_ms: float  # In milliseconds to match your game time!

class AnimationManager:
    def __init__(self, assets_path: str = "assets/video"):
        self.assets_path = Path(assets_path)
        self.animations: dict[str, Animation] = {}
        self.default_frame_duration_ms = 100.0  # 100ms per frame by default

    def get_frame_at_time(self, asset_name: str, elapsed_time_ms: float, loop: bool = True, custom_ms_per_frame: Optional[float] = None) -> Optional[pygame.Surface]:
        anim = self.load_animation(asset_name)
        if not anim or not anim.frames:
            return None

        total_frames = len(anim.frames)

        # 1. Use the custom speed if provided, otherwise use the animation's native speed
        duration_to_use = custom_ms_per_frame if custom_ms_per_frame else anim.frame_duration_ms

        # 2. Calculate the frame index based on that duration
        frame_index = int(elapsed_time_ms / duration_to_use)

        if not loop and frame_index >= total_frames:
            return None

        return anim.frames[frame_index % total_frames]

    def load_animation(self, animation_name: str, frame_count: Optional[int] = None) -> Optional[Animation]:
        if animation_name in self.animations:
            return self.animations[animation_name]

        frames: list[Any] = []
        frame_duration_ms = self.default_frame_duration_ms
        animation_dir = self.assets_path / animation_name
        gif_path = self.assets_path / f"{animation_name}.gif"

        if gif_path.exists():
            frames, frame_duration_ms = self._load_gif(gif_path)
        elif animation_dir.is_dir():
            frames = self._load_frames_from_directory(animation_dir, frame_count)
        else:
            frames = self._load_frames_from_files(animation_name, frame_count)

        if not frames:
            print(f"Warning: No animation frames or GIF found for '{animation_name}'")
            return None

        animation = Animation(frames=frames, frame_duration_ms=frame_duration_ms)
        self.animations[animation_name] = animation
        return animation

    def _load_gif(self, gif_path: Path) -> tuple[list[pygame.Surface], float]:
        frames = []
        try:
            pil_image = Image.open(gif_path)
            duration_ms = float(pil_image.info.get('duration', 100))

            for frame in ImageSequence.Iterator(pil_image):
                frame_rgba = frame.convert("RGBA")
                pygame_surface = pygame.image.fromstring(
                    frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode  #type:ignore
                ).convert_alpha()
                frames.append(pygame_surface)
            return frames, duration_ms
        except Exception as e:
            print(f"Error loading GIF '{gif_path}': {e}")
            return [], self.default_frame_duration_ms

    def _load_frames_from_directory(self, animation_dir: Path, frame_count: Optional[int]) -> list[pygame.Surface]:
        frames: list[Any] = []
        max_frames = frame_count if frame_count else 100
        start_index = 0 if any((animation_dir / p).exists() for p in ["0.png", "frame_0.png", "00.png"]) else 1
        frame_index = start_index

        while len(frames) < max_frames:
            frame_found = False
            for pattern in [f"{frame_index}.png", f"frame_{frame_index}.png", f"{frame_index:02d}.png"]:
                frame_path = animation_dir / pattern
                if frame_path.exists():
                    try:
                        frames.append(pygame.image.load(str(frame_path)).convert_alpha())
                        frame_found = True
                        break
                    except pygame.error:
                        pass
            if not frame_found: break
            frame_index += 1
        return frames

    def _load_frames_from_files(self, animation_name: str, frame_count: Optional[int]) -> list[pygame.Surface]:
        frames: list[Any] = []
        max_frames = frame_count if frame_count else 100
        start_index = 0
        if not any((self.assets_path / f"{animation_name}_{0}{ext}").exists() for ext in ['.png', '.jpg', '.jpeg']) and \
           not any((self.assets_path / f"{animation_name}_{0:02d}{ext}").exists() for ext in ['.png', '.jpg', '.jpeg']):
            start_index = 1

        frame_index = start_index

        while len(frames) < max_frames:
            frame_found = False
            for pattern in [f"{animation_name}_{frame_index}", f"{animation_name}_{frame_index:02d}"]:
                for ext in ['.png', '.jpg', '.jpeg']:
                    frame_path = self.assets_path / f"{pattern}{ext}"
                    if frame_path.exists():
                        try:
                            frames.append(pygame.image.load(str(frame_path)).convert_alpha())
                            frame_found = True
                            break
                        except pygame.error:
                            pass
                if frame_found: break
            if not frame_found: break
            frame_index += 1
        return frames