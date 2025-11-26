from src.frontend_client.pygame_renderer.draw_manager.window_manager.window_manager import WindowManager

class WindowManagerConfig:

    @staticmethod
    def create_window_manager() -> WindowManager:
        return WindowManager()