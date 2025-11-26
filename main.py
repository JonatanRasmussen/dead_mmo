from src.frontend_client.pygame_implementation.pygame_launcher import PygameLauncher
from src.game_loop_config import GameLoopConfig

#%%
if __name__ == "__main__":
    #PygameLauncher.run_game()
    game_loop = GameLoopConfig.create_game_loop()
    game_loop.temp_run_ingame_loop()