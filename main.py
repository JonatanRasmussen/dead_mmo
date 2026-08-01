from src import IngameLoop
import cProfile

#%%
def main() -> None:
    IngameLoop.temp_testing_delete_later()
    #IngameLoop.temp_main_delete_later()

if __name__ == "__main__":
    #cProfile.run("main()", sort="tottime")
    main()