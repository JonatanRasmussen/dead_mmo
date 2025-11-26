from src.frontend_client.ui_manager.ui_manager import UiManager


class UiManagerConfig:

    @staticmethod
    def create_ui_manager() -> UiManager:
        return UiManager()