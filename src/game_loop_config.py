from src.game_loop import GameLoop
from src.backend_access.backend_access_config import BackendAccessConfig
from src.frontend_client.frontend_client_config import FrontendClientConfig

class GameLoopConfig:

    @staticmethod
    def create_game_loop() -> GameLoop:
        server = BackendAccessConfig.create_local_backend()
        client = FrontendClientConfig.create_frontend_client()
        return GameLoop(server, client)