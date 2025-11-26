import pygame
import os
from typing import Dict, List, Optional, Tuple, ValuesView
from pathlib import Path
from dataclasses import dataclass

from src.models.events import FinalizedEvent


@dataclass
class Animation:
    """Represents an animated effect"""
    frames: list[pygame.Surface]
    frame_duration: float  # Duration of each frame in seconds
    loop: bool = False
    scale: float = 1.0

@dataclass
class ActiveAnimation:
    """Represents a currently playing animation"""
    animation: Animation
    x: float  # World coordinates
    y: float  # World coordinates
    current_frame: int = 0
    time_elapsed: float = 0.0
    total_duration: float = 0.0

class AnimationManager:
    def __init__(self, assets_path: str = "assets/animations"):
        self.assets_path = Path(assets_path)
        self.animations: dict[str, Animation] = {}
        self.active_animations: list[ActiveAnimation] = []
        self.default_frame_duration = 0.1  # 100ms per frame by default

    def load_animation(self, animation_name: str, frame_count: Optional[int] = None) -> Optional[Animation]:
        """Load an animation from multiple frame files or return cached version"""
        if animation_name in self.animations:
            return self.animations[animation_name]

        frames = []
        animation_dir = self.assets_path / animation_name

        # Try to load from a directory with numbered frames
        if animation_dir.is_dir():
            frames = self._load_frames_from_directory(animation_dir, frame_count)
        else:
            # Try to load from individual files with naming convention
            frames = self._load_frames_from_files(animation_name, frame_count)

        if not frames:
            print(f"Warning: No animation frames found for '{animation_name}'")
            return None

        # Create animation with default settings
        animation = Animation(
            frames=frames,
            frame_duration=self.default_frame_duration,
            loop=False,
            scale=1.0
        )

        self.animations[animation_name] = animation
        return animation

    def _load_frames_from_directory(self, animation_dir: Path, frame_count: Optional[int]) -> list[pygame.Surface]:
        """Load animation frames from a directory"""
        frames = []

        # Look for numbered files (0.png, 1.png, etc. or frame_0.png, frame_1.png, etc.)
        frame_index = 0
        max_frames = frame_count if frame_count else 100  # Reasonable limit

        while frame_index < max_frames:
            frame_found = False

            # Try different naming conventions
            for pattern in [f"{frame_index}.png", f"frame_{frame_index}.png", f"{frame_index:02d}.png"]:
                frame_path = animation_dir / pattern
                if frame_path.exists():
                    try:
                        frame = pygame.image.load(str(frame_path)).convert_alpha()
                        frames.append(frame)
                        frame_found = True
                        break
                    except pygame.error as e:
                        print(f"Error loading animation frame '{frame_path}': {e}")

            if not frame_found:
                break

            frame_index += 1

        return frames

    def _load_frames_from_files(self, animation_name: str, frame_count: Optional[int]) -> list[pygame.Surface]:
        """Load animation frames from individual files with naming convention"""
        frames = []
        frame_index = 0
        max_frames = frame_count if frame_count else 100

        while frame_index < max_frames:
            frame_found = False

            # Try different naming conventions and extensions
            for pattern in [f"{animation_name}_{frame_index}", f"{animation_name}_{frame_index:02d}"]:
                for ext in ['.png', '.jpg', '.jpeg']:
                    frame_path = self.assets_path / f"{pattern}{ext}"
                    if frame_path.exists():
                        try:
                            frame = pygame.image.load(str(frame_path)).convert_alpha()
                            frames.append(frame)
                            frame_found = True
                            break
                        except pygame.error as e:
                            print(f"Error loading animation frame '{frame_path}': {e}")
                if frame_found:
                    break

            if not frame_found:
                break

            frame_index += 1

        return frames

    def process_events(self, finalized_events: ValuesView[FinalizedEvent]) -> None:
        """Process all finalized events and start animations for events that should play animations"""
        for event in finalized_events:
            if event.should_play_animation:
                # Get position from event (you might need to adjust these attribute names)
                x = getattr(event, 'x', 0.5)  # Default to center if no position
                y = getattr(event, 'y', 0.5)
                scale = getattr(event, 'animation_scale', 1.0)

                self.start_animation(event.animation_name, x, y, scale)

    def start_animation(self, animation_name: str, x: float, y: float, scale: float = 1.0) -> bool:
        """Start playing an animation at the specified world coordinates"""
        animation = self.load_animation(animation_name)
        if not animation:
            return False

        # Create a copy of the animation with the specified scale
        scaled_animation = Animation(
            frames=[pygame.transform.scale(frame,
                   (int(frame.get_width() * scale), int(frame.get_height() * scale)))
                   for frame in animation.frames],
            frame_duration=animation.frame_duration,
            loop=animation.loop,
            scale=scale
        )

        active_animation = ActiveAnimation(
            animation=scaled_animation,
            x=x,
            y=y,
            total_duration=len(scaled_animation.frames) * scaled_animation.frame_duration
        )

        self.active_animations.append(active_animation)
        return True

    def update(self, delta_time: float) -> None:
        """Update all active animations"""
        animations_to_remove = []

        for i, active_anim in enumerate(self.active_animations):
            active_anim.time_elapsed += delta_time

            # Calculate current frame
            frame_time = active_anim.time_elapsed / active_anim.animation.frame_duration
            active_anim.current_frame = int(frame_time) % len(active_anim.animation.frames)

            # Check if animation is finished
            if not active_anim.animation.loop and active_anim.time_elapsed >= active_anim.total_duration:
                animations_to_remove.append(i)

        # Remove finished animations (in reverse order to maintain indices)
        for i in reversed(animations_to_remove):
            del self.active_animations[i]

    def render(self, screen: pygame.Surface, window_manager) -> None:
        """Render all active animations"""
        for active_anim in self.active_animations:
            if active_anim.current_frame < len(active_anim.animation.frames):
                frame = active_anim.animation.frames[active_anim.current_frame]

                # Convert world coordinates to screen coordinates
                screen_pos = window_manager.world_to_screen_coords(active_anim.x, active_anim.y)

                # Center the frame on the position
                frame_rect = frame.get_rect(center=screen_pos)
                screen.blit(frame, frame_rect)

    def clear_all_animations(self) -> None:
        """Clear all active animations"""
        self.active_animations.clear()

    def set_default_frame_duration(self, duration: float) -> None:
        """Set the default frame duration for new animations"""
        self.default_frame_duration = duration

    def preload_animations(self, animation_names: list[str]) -> None:
        """Preload a list of animations"""
        for animation_name in animation_names:
            self.load_animation(animation_name)