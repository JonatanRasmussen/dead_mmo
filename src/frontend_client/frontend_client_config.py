from src.frontend_client.frontend_client import FrontendClient
from src.frontend_client.pygame_renderer.pygame_renderer_config import PygameRendererConfig
from src.frontend_client.ui_manager.ui_manager_config import UiManagerConfig


class FrontendClientConfig:

    @staticmethod
    def create_frontend_client() -> FrontendClient:
        new_render = PygameRendererConfig.create_pygame_rendering_framework()
        ui_manager = UiManagerConfig.create_ui_manager()
        return FrontendClient(new_render, ui_manager)