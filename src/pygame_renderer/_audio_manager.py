import pygame
import os
from typing import Dict, Optional, ValuesView
from pathlib import Path

class AudioManager:
    def __init__(self, assets_path: str = "assets/audio"):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)  # Increased to allow more simultaneous sounds
        self.assets_path = Path(assets_path)
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.sound_volume = 0.1

        # Track active channels by obj_id: { obj_id: (audio_name, audio_start, channel) }
        self._active_channels: dict[int, tuple[str, int, pygame.mixer.Channel]] = {}

    def play_sound(self, audio_name: str) -> None:
        """Play a sound effect immediately (fire-and-forget)."""
        sound = self.load_sound(audio_name)
        if sound:
            sound.play()

    def update_audio(self, obj_id: int, audio_name: str, audio_start: int, audio_loop: bool, frame_start: int) -> None:
        """State-driven audio update. Stops old sounds if state changes, starts new sounds if triggered."""

        # 1. Check if we need to stop a currently tracked audio for this obj_id
        if obj_id in self._active_channels:
            active_audio_name, active_audio_start, channel = self._active_channels[obj_id]

            expected_sound = self.sounds.get(active_audio_name)

            # If the channel is idle, or Pygame reused it for a different sound, it's a stale reference.
            if not channel.get_busy() or channel.get_sound() != expected_sound:
                del self._active_channels[obj_id]

            # Otherwise, if the game state says this audio should change/stop, stop it.
            elif active_audio_name != audio_name or active_audio_start != audio_start:
                channel.stop()
                del self._active_channels[obj_id]

        # 2. Check if we need to start new audio
        # We only start if audio_name is not empty and audio_start triggered this frame
        if audio_name and audio_start >= frame_start:

            # Prevent double-playing if it was already started this exact frame
            if obj_id in self._active_channels and self._active_channels[obj_id][1] == audio_start:
                return

            sound = self.load_sound(audio_name)
            if sound:
                loops = -1 if audio_loop else 0
                channel = sound.play(loops=loops)

                # Track the channel so it can be interrupted if the state changes!
                if channel:
                    self._active_channels[obj_id] = (audio_name, audio_start, channel)

    def load_sound(self, audio_name: str) -> Optional[pygame.mixer.Sound]:
        """Load a sound from file or return cached version"""
        if audio_name in self.sounds:
            return self.sounds[audio_name]
        for ext in ['.wav', '.ogg', '.mp3']:
            audio_path = self.assets_path / f"{audio_name}{ext}"
            if audio_path.exists():
                try:
                    sound = pygame.mixer.Sound(str(audio_path))
                    sound.set_volume(self.sound_volume)
                    self.sounds[audio_name] = sound
                    return sound
                except pygame.error as e:
                    print(f"Error loading sound '{audio_name}': {e}")
                    continue
        print(f"Warning: Sound '{audio_name}' not found in {self.assets_path}")
        return None

    def set_sound_volume(self, volume: float) -> None:
        """Set volume for sound effects (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)