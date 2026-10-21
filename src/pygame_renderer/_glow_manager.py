import pygame
import math
from typing import Optional

class GlowManager:
    """Handles caching and generation of glow and neon effects."""

    def __init__(self) -> None:
        # Restored old SVG glow image cache
        self._glow_img: Optional[pygame.Surface] = None

        # Caches for our programmatic neon glows
        self._neon_glow_cache: dict[tuple[int, int, int], pygame.Surface] = {}
        # Cache for scaled versions to prevent CPU lag with many objects
        self._scaled_neon_cache: dict[tuple[tuple[int, int, int], int], pygame.Surface] = {}

    def get_glow_img(self) -> pygame.Surface:
        """Lazy init glow image, requires pygame to be running"""
        if self._glow_img is None:
            self._glow_img = self._load_glow_effect()
        return self._glow_img

    @staticmethod
    def _load_glow_effect() -> pygame.Surface:
        try:
            glow_img = pygame.image.load("assets/images/Food.svg").convert_alpha()
            PADDING = 2
            w, h = glow_img.get_size()
            padded = pygame.Surface((w + PADDING * 2, h + PADDING * 2), pygame.SRCALPHA)
            padded.blit(glow_img, (PADDING, PADDING))
            return padded
        except FileNotFoundError:
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 100), (32, 32), 32)
            return surf

    def get_scaled_neon_glow(self, color_rgb: tuple[int, int, int], diameter: int) -> pygame.Surface:
        """Returns a scaled neon glow surface, utilizing a cache to prevent CPU lag."""
        cache_key = (color_rgb, diameter)
        if cache_key in self._scaled_neon_cache:
            return self._scaled_neon_cache[cache_key]

        # If not in cache, get the base 128x128 glow and scale it
        base_glow = self._get_base_neon_glow(color_rgb)
        scaled_glow = pygame.transform.smoothscale(base_glow, (diameter, diameter))

        # Save it for next time
        self._scaled_neon_cache[cache_key] = scaled_glow
        return scaled_glow

    def _get_base_neon_glow(self, color_rgb: tuple[int, int, int]) -> pygame.Surface:
        """Precomputes a smooth, high-fidelity Gaussian-style neon radial texture."""
        if color_rgb in self._neon_glow_cache:
            return self._neon_glow_cache[color_rgb]

        size = 128
        radius = size // 2

        # Use a standard surface with a pure black background.
        # In BLEND_ADD, black (0,0,0) acts as completely transparent!
        glow_surf = pygame.Surface((size, size))
        glow_surf.fill((0, 0, 0))

        # 64 micro-layers eliminate banding completely
        steps = 64
        for i in range(steps, 0, -1):
            t = i / steps
            r = int(radius * t)

            # Exponential decay curve (simulates inverse-square light dissipation)
            intensity = math.exp(-4.0 * t)

            # Near the center (t < 0.25), shift color towards pure white for the hot core
            core_factor = max(0.0, 1.0 - (t / 0.25)) ** 2
            base_r = color_rgb[0] + (255 - color_rgb[0]) * core_factor * 0.85
            base_g = color_rgb[1] + (255 - color_rgb[1]) * core_factor * 0.85
            base_b = color_rgb[2] + (255 - color_rgb[2]) * core_factor * 0.85

            # PRE-MULTIPLY the RGB values by the intensity.
            # This physically darkens the pixels towards the edge, which is how additive blending works.
            final_r = min(255, int(base_r * intensity * 0.8))
            final_g = min(255, int(base_g * intensity * 0.8))
            final_b = min(255, int(base_b * intensity * 0.8))

            # Draw solid circles from outside in. Because we draw largest to smallest,
            # they stack perfectly into a gradient.
            pygame.draw.circle(glow_surf, (final_r, final_g, final_b), (radius, radius), r)

        self._neon_glow_cache[color_rgb] = glow_surf
        return glow_surf