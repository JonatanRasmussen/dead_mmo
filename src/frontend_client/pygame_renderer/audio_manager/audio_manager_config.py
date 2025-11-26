from src.frontend_client.pygame_renderer.audio_manager.audio_manager import AudioManager

class AudioManagerConfig:

    @staticmethod
    def create_audio_manager() -> AudioManager:
        return AudioManager()