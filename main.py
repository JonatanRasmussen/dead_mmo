from src import IngameLoop
import cProfile

#%%
def main() -> None:
    setup_spell_ids: list[int] = IngameLoop.TEST_SETUP_SPELL_IDS
    ingame_loop = IngameLoop()
    ingame_loop.play_game_in_pygame(setup_spell_ids)

if __name__ == "__main__":
    #cProfile.run("main()", sort="tottime")
    main()