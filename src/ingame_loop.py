from .pygame_renderer import PygameRenderer
from src.settings import Consts
from src.world_state.world_state import DisplayObj, WorldState


class IngameLoop:

    @staticmethod
    def play_game_in_pygame(setup_spell_ids: list[int], scripted_player_input: dict[int, list[str]] | None = None) -> None:

        # Initialization
        rendering_framework = PygameRenderer()
        rendering_framework.launch_rendering_framework()
        current_ingame_time = 0
        rounding_error = 0.0
        cached_irl_time = rendering_framework.get_current_time()
        world_state = WorldState()
        assert len(setup_spell_ids) == 2, f"Unsupported amount of setup_spell_ids ({len(setup_spell_ids)}), for now the game only supports 1 boss and 1 player"
        boss1_setup_spell_id = setup_spell_ids[0]
        player1_setup_spell_id = setup_spell_ids[1]
        _boss1_obj_id = world_state.register_player(current_ingame_time, boss1_setup_spell_id)
        player1_obj_id = world_state.register_player(current_ingame_time, player1_setup_spell_id)
        player_inputs_this_frame: list[str] = []
        while rendering_framework.is_running():
            # Update time (and because smallest in-game timeunit is 1ms, ensure rounding error stays +/- 1ms throughout the game)
            current_irl_time = rendering_framework.get_current_time()
            exact_irl_elapsed_time_ms = (current_irl_time - cached_irl_time) * Consts.TIMESTAMPS_PER_SECOND + rounding_error
            ingame_time_elapsed_this_frame = int(round(exact_irl_elapsed_time_ms))  # round to smallest allowed in-game time unit
            rounding_error = exact_irl_elapsed_time_ms - ingame_time_elapsed_this_frame
            if ingame_time_elapsed_this_frame < 1:
                rounding_error += exact_irl_elapsed_time_ms - 1
                ingame_time_elapsed_this_frame = 1
            cached_irl_time = current_irl_time
            current_ingame_time += ingame_time_elapsed_this_frame
            ingame_time_at_frame_start = current_ingame_time - ingame_time_elapsed_this_frame

            player_inputs_this_frame.clear()
            if scripted_player_input is None:
                current_inputs: list[str] = rendering_framework.fetch_player_input()
                if current_inputs:
                    player_inputs_this_frame.extend(current_inputs)
            else:
                # Player is NOT controlling game; scripted player input is used instead (for testing purposes)
                _ = rendering_framework.fetch_player_input()  # Only called to allow Escape keypress to close game
                for timestamp, inputs in scripted_player_input.items():
                    if ingame_time_at_frame_start < timestamp <= current_ingame_time:
                        player_inputs_this_frame.extend(inputs)

            # Simulate next frame
            world_state.process_frame(player1_obj_id, player_inputs_this_frame, current_ingame_time)
            # Render the frame we just simulated
            rendering_framework.begin_frame()
            display_objs_dct = world_state.get_display_obj_dct(current_ingame_time)
            for display_obj in display_objs_dct.values():
                IngameLoop._render_game_obj(rendering_framework, display_obj, ingame_time_at_frame_start, current_ingame_time)
            rendering_framework.end_frame()

        # Cleanup when exiting game
        rendering_framework.terminate_rendering_framework()


    @staticmethod
    def _render_game_obj(rendering_framework: PygameRenderer, display_obj: DisplayObj, frame_start: int, frame_end: int) -> None:
        if display_obj.is_visible:
            rendering_framework.draw_blinking_circle(
                pos_xy=display_obj.pos_xy,
                scale=display_obj.size,
                color_rgb=display_obj.color_rgb,
                time_ms=rendering_framework.get_current_time(),
                asset_name=display_obj.sprite_name,
        )
        if display_obj.audio_id and display_obj.audio_start > frame_start:
            rendering_framework.play_sound(display_obj.audio_name)
        if display_obj.animation_id:
            elapsed_time_ms = float(frame_end - display_obj.animation_start)
            rendering_framework.draw_animation(
                display_obj.pos_xy,
                display_obj.animation_scale,
                display_obj.animation_name,
                elapsed_time_ms,
                display_obj.animation_ms_per_frame,
            )