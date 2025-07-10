import pygame
import os
from typing import Dict, Optional, ValuesView
from pathlib import Path

from src.models.components import GameObj
from src.models.events import FinalizedEvent

class AudioManager:
    def __init__(self, assets_path: str = "src/assets/audio"):
        pygame.mixer.init()
        self.assets_path = Path(assets_path)
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_volume = 0.7
        self.sound_volume = 0.7

    def load_sound(self, audio_name: str) -> Optional[pygame.mixer.Sound]:
        """Load a sound from file or return cached version"""
        if audio_name in self.sounds:
            return self.sounds[audio_name]

        # Try to load the sound
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

    def process_events(self, finalized_events: ValuesView[FinalizedEvent]) -> None:
        """Process all finalized events and play audio for events that should play audio"""
        for event in finalized_events:
            if event.should_play_audio:
                self.play_sound(event.audio_name)

    def play_sound(self, audio_name: str) -> None:
        """Play a sound effect"""
        sound = self.load_sound(audio_name)
        if sound:
            sound.play()

    def play_music(self, audio_name: str, loops: int = -1) -> None:
        """Play background music"""
        for ext in ['.wav', '.ogg', '.mp3']:
            audio_path = self.assets_path / f"{audio_name}{ext}"
            if audio_path.exists():
                try:
                    pygame.mixer.music.load(str(audio_path))
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(loops)
                    return
                except pygame.error as e:
                    print(f"Error loading music '{audio_name}': {e}")
                    continue

        print(f"Warning: Music '{audio_name}' not found in {self.assets_path}")

    def stop_music(self) -> None:
        """Stop background music"""
        pygame.mixer.music.stop()

    def set_sound_volume(self, volume: float) -> None:
        """Set volume for sound effects (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)

    def set_music_volume(self, volume: float) -> None:
        """Set volume for background music (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)