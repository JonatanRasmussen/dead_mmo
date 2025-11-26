from src.frontend_client.pygame_renderer.input_handler.input_handler import InputHandler

class InputHandlerConfig:

    @staticmethod
    def create_input_handler() -> InputHandler:
        return InputHandler()