import pygame
import os
from typing import Dict, Optional
from pathlib import Path

class SpriteManager:
    def __init__(self, assets_path: str = "src/assets/images"):
        self.assets_path = Path(assets_path)
        self.sprites: dict[str, pygame.Surface] = {}
        self.default_sprite: pygame.Surface = self._create_default_sprite()
        self._create_default_sprite()

    def load_sprite(self, sprite_name: str) -> pygame.Surface:
        """Load a sprite from file or return cached version"""
        if sprite_name in self.sprites:
            return self.sprites[sprite_name]

        # Try to load the sprite
        sprite_path = self.assets_path / f"{sprite_name}.png"

        try:
            if sprite_path.exists():
                sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.sprites[sprite_name] = sprite
                return sprite
            else:
                # Try without extension
                for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                    alt_path = self.assets_path / f"{sprite_name}{ext}"
                    if alt_path.exists():
                        sprite = pygame.image.load(str(alt_path)).convert_alpha()
                        self.sprites[sprite_name] = sprite
                        return sprite

                print(f"Warning: Sprite '{sprite_name}' not found in {self.assets_path}")
                return self.default_sprite
        except pygame.error as e:
            print(f"Error loading sprite '{sprite_name}': {e}")
            return self.default_sprite

    def get_sprite(self, sprite_name: str) -> pygame.Surface:
        """Get a sprite, loading it if necessary"""
        return self.load_sprite(sprite_name)

    def preload_sprites(self, sprite_names: list[str]) -> None:
        """Preload a list of sprites"""
        for sprite_name in sprite_names:
            self.load_sprite(sprite_name)

    def _create_default_sprite(self) -> pygame.Surface:
        """Create a default sprite for missing assets"""
        default_sprite = pygame.Surface((32, 32))
        default_sprite.fill((255, 0, 255))  # Magenta for missing sprites
        return default_sprite