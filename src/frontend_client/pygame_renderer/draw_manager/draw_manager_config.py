from src.frontend_client.pygame_renderer.draw_manager.draw_manager import DrawManager
from src.frontend_client.pygame_renderer.draw_manager.window_manager.window_manager_config import WindowManagerConfig
from src.frontend_client.pygame_renderer.draw_manager.sprite_manager.sprite_manager_config import SpriteManagerConfig
from src.frontend_client.pygame_renderer.draw_manager.animation_manager.animation_manager_config import AnimationManagerConfig

class DrawManagerConfig:

    @staticmethod
    def create_draw_manager() -> DrawManager:
        window_manager = WindowManagerConfig.create_window_manager()
        sprite_manager = SpriteManagerConfig.create_sprite_manager()
        animation_manager = AnimationManagerConfig.create_animation_manager()
        return DrawManager(window_manager, sprite_manager, animation_manager)