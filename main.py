from src import IngameLoop
import cProfile

#%%
def main() -> None:
    ingame_loop: IngameLoop = IngameLoop()
    ingame_loop.run()

if __name__ == "__main__":
    #cProfile.run("main()", sort="tottime")
    main()