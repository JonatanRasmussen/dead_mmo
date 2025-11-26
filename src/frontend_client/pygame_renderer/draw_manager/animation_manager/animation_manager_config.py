from src.frontend_client.pygame_renderer.draw_manager.animation_manager.animation_manager import AnimationManager

class AnimationManagerConfig:

    @staticmethod
    def create_animation_manager() -> AnimationManager:
        return AnimationManager()