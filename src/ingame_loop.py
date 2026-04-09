from _collections_abc import Iterable
from typing import Protocol
from typing_extensions import override
from .models.data import Spell
from .models.handlers.spell_database import SpellDatabase
from .backend_server import BackendServer
from .pygame_renderer import PygameRenderer
from .ui_manager import UiManager


class IngameLoop:

    def __init__(self) -> None:
        self._server = BackendServer()
        self._rendering_framework = PygameRenderer()
        self._ui_manager = UiManager()
        self._cached_time: float = self._rendering_framework.get_current_time()
        self._temp_spell_db: SpellDatabase = SpellDatabase()

    def run(self) -> None:
        self._rendering_framework.launch_rendering_framework()
        while self._rendering_framework.is_running():
            player_input = self._rendering_framework.fetch_player_input()
            self._server.send_player_input(player_input)
            elapsed_time = self._get_elapsed_time()
            self._server.simulate_next_frame(elapsed_time)

            self._rendering_framework.begin_frame()
            while True:
                event_tuple = self._server.request_updated_event()
                if event_tuple is None:
                    break
                self._apply_event(*event_tuple)
            while True:
                game_obj_update = self._server.request_updated_obj()
                if game_obj_update is None:
                    break
                self._render_game_obj(*game_obj_update)
            self._render_frame_actions()
            self._rendering_framework.end_frame()

        self._rendering_framework.terminate_rendering_framework()

    def _get_elapsed_time(self) -> float:
        current_time = self._rendering_framework.get_current_time()
        elapsed_time = current_time - self._cached_time
        self._cached_time = current_time
        return elapsed_time

    def _apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int, modifier: float, succesful_outcome: bool) -> None:
        # NOT YET FULLY IMPLEMENTED
        #self._ui_manager.apply_ui_update(serialized_event)
        spell: Spell = self._temp_spell_db.get_spell(spell_id)
        if spell.should_play_audio and succesful_outcome:
            self._rendering_framework.play_sound(spell.audio_name)
        if spell.should_play_animation and succesful_outcome:
            pos = (0.0, 0.0) #pos = (f_event.effect_position.x, f_event.effect_position.y)
            self._rendering_framework.play_animation(
                pos_xy=pos,
                scale=spell.animation_scale,
                asset_name=spell.animation_name
            )

    def _render_game_obj(self, pos_xy: tuple[float, float], obj_size: float, color: tuple[int, int, int], sprite_name: str | None, is_visible: bool) -> None:
        if is_visible:
            self._rendering_framework.draw_blinking_circle(
                pos_xy=pos_xy,
                scale=obj_size,
                color_rgb=color,
                time_ms=self._rendering_framework.get_current_time(),
                asset_name=sprite_name
            )

    def _render_frame(self) -> None:
        self._rendering_framework.begin_frame()
        self._render_frame_actions()
        self._rendering_framework.end_frame()

    def _render_frame_actions(self) -> None:
        # temp obj draw logic, remove later
        pass
        # continue with the proper (but not yet implemented) logic
        for rend_act in self._ui_manager.get_render_actions():
            if rend_act.is_type_circle():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.draw_circle(rend_act.pos_xy, scale, rend_act.color_rgb, rend_act.asset_name)
            elif rend_act.is_type_rectangle():
                self._rendering_framework.draw_rectangle(rend_act.pos_xy, rend_act.scale_xy, rend_act.color_rgb, rend_act.asset_name)
            elif rend_act.is_type_animation():
                scale = rend_act.convert_scale_xy_to_scale()
                self._rendering_framework.play_animation(rend_act.pos_xy, scale, rend_act.asset_name)
            elif rend_act.is_type_text():
                font_size = rend_act.convert_scale_xy_to_font_size()
                self._rendering_framework.display_text(rend_act.pos_xy, font_size, rend_act.color_rgb, rend_act.text_to_display)
            elif rend_act.is_type_audio():
                self._rendering_framework.play_sound(rend_act.asset_name)
        self._ui_manager.clear_current_frame_event_cache()