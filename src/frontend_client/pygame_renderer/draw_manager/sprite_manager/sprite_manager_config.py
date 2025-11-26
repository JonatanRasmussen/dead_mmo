from src.frontend_client.pygame_renderer.draw_manager.sprite_manager.sprite_manager import SpriteManager

class SpriteManagerConfig:

    @staticmethod
    def create_sprite_manager() -> SpriteManager:
        return SpriteManager()