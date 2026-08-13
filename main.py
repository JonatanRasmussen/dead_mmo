from src.old_ingame_loop import OldIngameLoop
from src.ingame_loop import IngameLoop
from src.settings import LevelSetupConsts
from tests.old_sim_validation import OldSimValidation
from tests.sim_validation import SimValidation
import cProfile

#%%
def old_main() -> None:
    # Run old tests
    OldSimValidation.simulate_game_in_console(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS,
            LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
        )
    # Actually play the play
    OldIngameLoop.play_game_in_pygame(
        LevelSetupConsts.TEST_SETUP_SPELL_IDS,
        LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
    )

def main() -> None:
    # Run tests
    SimValidation.simulate_game_in_console(
            LevelSetupConsts.TEST_SETUP_SPELL_IDS,
            LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
        )
    # Actually play the play
    IngameLoop.new_play_game_in_pygame(
        LevelSetupConsts.TEST_SETUP_SPELL_IDS,
        LevelSetupConsts.SCRIPTED_PLAYER_INPUT_FOR_TESTING
    )

if __name__ == "__main__":
    #cProfile.run("main()", sort="tottime")
    main()