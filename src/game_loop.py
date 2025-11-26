from typing import Protocol, ValuesView

class IBackendAccess(Protocol):
    """ Access to a game kernel, either locally hosted or on a remote server """
    def send_player_input(self, serialized_input: str) -> None: ...
    def request_updated_events(self, elapsed_time: float) -> list[str]: ...
    def request_serialized_game_state(self) -> list[str]: ...

class IFrontendClient(Protocol):
    def launch_rendering_framework(self) -> None: ...
    def terminate_rendering_framework(self) -> None: ...
    def is_running(self) -> bool: ...
    def fetch_player_input(self) -> str: ...
    def get_elapsed_time(self) -> float: ...
    def apply_events(self, serialized_events: list[str]) -> None: ...
    def render_frame(self) -> None: ...
    def apply_serialized_game_state(self, serialized_objs: list[str]) -> None: ...

class IGameLoop(Protocol):
    def run_ingame_loop(self) -> None: ...
    def temp_run_ingame_loop(self) -> None: ...

class GameLoop(IGameLoop):

    def __init__(self, server: IBackendAccess, client: IFrontendClient) -> None:
        self._server: IBackendAccess = server
        self._client: IFrontendClient = client

    def run_ingame_loop(self) -> None:
        self._client.launch_rendering_framework()
        while self._client.is_running():
            self._server.send_player_input(self._client.fetch_player_input())
            self._client.apply_events(self._server.request_updated_events(self._client.get_elapsed_time()))
            self._client.render_frame()
        self._client.terminate_rendering_framework()

    def temp_run_ingame_loop(self) -> None:
        self._client.launch_rendering_framework()
        while self._client.is_running():
            self._server.send_player_input(self._client.fetch_player_input())
            events = self._server.request_updated_events(self._client.get_elapsed_time())
            self._client.apply_events(events)
            game_state = self._server.request_serialized_game_state()
            self._client.apply_serialized_game_state(game_state)
            self._client.render_frame()
        self._client.terminate_rendering_framework()