from src import IngameLoop
import cProfile

#%%
def main() -> None:
    setup_spell_ids: list[int] = IngameLoop.TEST_SETUP_SPELL_IDS
    scripted_player_input_for_testing = IngameLoop.SCRIPTED_PLAYER_INPUT_FOR_TESTING
    simulated_ingame_loop = IngameLoop()
    simulated_ingame_loop.simulate_game_in_console(setup_spell_ids,scripted_player_input_for_testing)
    rendered_ingame_loop = IngameLoop()
    #ingame_loop.play_game_in_pygame(setup_spell_ids, scripted_player_input_for_testing)
    rendered_ingame_loop.play_game_in_pygame(setup_spell_ids)

if __name__ == "__main__":
    #cProfile.run("main()", sort="tottime")
    main()