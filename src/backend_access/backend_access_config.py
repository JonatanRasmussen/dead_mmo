from src.backend_access.local_server import LocalBackend

class BackendAccessConfig:
    @staticmethod
    def create_local_backend() -> LocalBackend:
        return LocalBackend()