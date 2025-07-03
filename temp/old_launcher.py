# pylint: disable=E1101
import pygame
import sys

class OldColor:
    BLACK: tuple[int, int, int] = (0, 0, 0)
    WHITE: tuple[int, int, int] = (255, 255, 255)
    RED: tuple[int, int, int] = (255, 0, 0)
    GREEN: tuple[int, int, int] = (0, 255, 0)
    BLUE: tuple[int, int, int] = (0, 0, 255)

class OldGameObj:
    def __init__(self) -> None:
        self.obj_id: int = 0

        self.pos_x: float = 0.0
        self.pos_y: float = 0.0

        self.size: float = 1.0
        self.power: float = 1.0
        self.movespeed: float = 0.01

        self.color: tuple[int, int, int] = OldColor.BLUE

    @classmethod
    def create_empty(cls) -> 'OldGameObj':
        return OldGameObj()

    @classmethod
    def create_player(cls) -> 'OldGameObj':
        obj = OldGameObj()
        obj.obj_id = 1
        obj.size = 0.02
        obj.movespeed = 0.01
        obj.color = OldColor.BLUE
        return obj

    @classmethod
    def create_enemy(cls) -> 'OldGameObj':
        obj = OldGameObj()
        obj.obj_id = 2
        obj.size = 0.1
        obj.movespeed = 0.005
        obj.color = OldColor.RED
        return obj

    def reposition(self, rel_x: float, rel_y: float) -> None:
        self.pos_x = rel_x
        self.pos_y = rel_y



class OldEncounter:
    def __init__(self) -> None:
        self.player: OldGameObj = OldGameObj.create_player()
        self.enemy: OldGameObj = OldGameObj.create_enemy()
        self.all_game_objs: list[OldGameObj] = [self.player, self.enemy]

        self.player.reposition(0.5, 0.75)
        self.enemy.reposition(0.5, 0.25)

    @classmethod
    def create_test_encounter(cls) -> 'OldEncounter':
        return OldEncounter()

class OldUtils:
    @staticmethod
    def clamp_position(obj: OldGameObj) -> None:
        obj.pos_x = max(0, min(1.0, obj.pos_x))
        obj.pos_y = max(0, min(1.0, obj.pos_y))

class OldLauncher:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("placeholder")
        self.WINDOW_WIDTH = 1920
        self.WINDOW_HEIGHT = 1080

        self.BORDER_TOP = 0.1
        self.BORDER_BOT = 0.2
        self.BORDER_SIDES = 0.05
        self.PLAY_RATIO = 1/1

        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.encounter = OldEncounter.create_test_encounter()
        self.running = True

        # Calculate play area dimensions and adjusted borders
        self.calculate_play_area()

    def calculate_play_area(self) -> None:
        # Calculate maximum possible play area dimensions considering minimum borders
        max_play_width = self.WINDOW_WIDTH * (1 - 2 * self.BORDER_SIDES)
        max_play_height = self.WINDOW_HEIGHT * (1 - self.BORDER_TOP - self.BORDER_BOT)

        # Calculate actual play area dimensions maintaining ratio
        if max_play_width/max_play_height > self.PLAY_RATIO:
            # Too wide, adjust width
            self.PLAY_HEIGHT = max_play_height
            self.PLAY_WIDTH = self.PLAY_HEIGHT * self.PLAY_RATIO
            # Center horizontally with extra border
            extra_width = max_play_width - self.PLAY_WIDTH
            self.BORDER_SIDES = self.BORDER_SIDES + (extra_width / (2 * self.WINDOW_WIDTH))
        else:
            # Too tall, adjust height
            self.PLAY_WIDTH = max_play_width
            self.PLAY_HEIGHT = self.PLAY_WIDTH / self.PLAY_RATIO
            # Center vertically with extra border
            extra_height = max_play_height - self.PLAY_HEIGHT
            extra_top = extra_height / 2
            self.BORDER_TOP = self.BORDER_TOP + (extra_top / self.WINDOW_HEIGHT)
            self.BORDER_BOT = self.BORDER_BOT + (extra_top / self.WINDOW_HEIGHT)

        # Calculate movement speed adjustment factors
        aspect_ratio = self.PLAY_WIDTH / self.PLAY_HEIGHT
        if aspect_ratio > 1:
            # Wider than tall - adjust horizontal movement
            self.movement_adjustment_x = 1.0 / aspect_ratio
            self.movement_adjustment_y = 1.0
        else:
            # Taller than wide - adjust vertical movement
            self.movement_adjustment_x = 1.0
            self.movement_adjustment_y = aspect_ratio


    def run_game(self) -> None:
        while self.running:
            self.take_player_input()
            self.draw_screen()
            pygame.time.Clock().tick(60)
        pygame.quit()
        sys.exit()

    def take_player_input(self) -> None:
        keys = pygame.key.get_pressed()
        player = self.encounter.player
        enemy = self.encounter.enemy

        # Apply movement with speed adjustments
        if keys[pygame.K_w]:
            player.pos_y -= player.movespeed * self.movement_adjustment_y
        if keys[pygame.K_s]:
            player.pos_y += player.movespeed * self.movement_adjustment_y
        if keys[pygame.K_a]:
            player.pos_x -= player.movespeed * self.movement_adjustment_x
        if keys[pygame.K_d]:
            player.pos_x += player.movespeed * self.movement_adjustment_x

        if keys[pygame.K_1]:
            enemy.size -= 0.001
        if keys[pygame.K_2]:
            player.size += 0.001
        if keys[pygame.K_3]:
            player.movespeed += 0.001
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

    def draw_screen(self) -> None:
        self.screen.fill(OldColor.WHITE)
        top = int(self.WINDOW_HEIGHT * self.BORDER_TOP)
        bot = int(self.WINDOW_HEIGHT * self.BORDER_BOT)
        sides = int(self.WINDOW_WIDTH * self.BORDER_SIDES)
        pygame.draw.rect(self.screen, OldColor.BLACK, (0, 0, self.WINDOW_WIDTH, top))
        pygame.draw.rect(self.screen, OldColor.BLACK, (0, self.WINDOW_HEIGHT - bot, self.WINDOW_WIDTH, bot))
        pygame.draw.rect(self.screen, OldColor.BLACK, (0, 0, sides, self.WINDOW_HEIGHT))
        pygame.draw.rect(self.screen, OldColor.BLACK, (self.WINDOW_WIDTH - sides, 0, sides, self.WINDOW_HEIGHT))

        for game_obj in self.encounter.all_game_objs:
            OldUtils.clamp_position(game_obj)
            self.draw_object(game_obj)
        pygame.display.flip()

    def draw_object(self, game_obj: OldGameObj) -> None:
        # Convert from unit coordinates (0-1) to screen coordinates
        screen_x = self.BORDER_SIDES * self.WINDOW_WIDTH + game_obj.pos_x * self.PLAY_WIDTH
        screen_y = self.BORDER_TOP * self.WINDOW_HEIGHT + game_obj.pos_y * self.PLAY_HEIGHT
        pos = (int(screen_x), int(screen_y))
        size = int(game_obj.size * self.PLAY_HEIGHT)
        pygame.draw.circle(self.screen, game_obj.color, pos, size)
if __name__ == "__main__":
    OldLauncher().run_game()