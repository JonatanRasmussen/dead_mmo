from src.frontend_client.pygame_renderer.pygame_renderer import PygameRenderer
from src.frontend_client.pygame_renderer.input_handler.input_handler_config import InputHandlerConfig
from src.frontend_client.pygame_renderer.draw_manager.draw_manager_config import DrawManagerConfig
from src.frontend_client.pygame_renderer.audio_manager.audio_manager_config import AudioManagerConfig

class PygameRendererConfig:

    @staticmethod
    def create_pygame_rendering_framework() -> PygameRenderer:
        input_handler = InputHandlerConfig.create_input_handler()
        draw_manager = DrawManagerConfig.create_draw_manager()
        audio_manager = AudioManagerConfig.create_audio_manager()
        return PygameRenderer(input_handler, draw_manager, audio_manager)