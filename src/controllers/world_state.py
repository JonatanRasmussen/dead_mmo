from typing import List, Tuple, ValuesView

from src.models import Aura, Controls, GameObj, ImportantIDs, UpcomingEvent, FinalizedEvent, Spell
from src.handlers import AuraHandler, ControlsHandler, GameObjHandler, SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._ingame_time: float = 0.0
        self._auras: AuraHandler = AuraHandler()
        self._controls: ControlsHandler = ControlsHandler()
        self._game_objs: GameObjHandler = GameObjHandler()

        self._spell_database: SpellDatabase = SpellDatabase()

    @property
    def get_ingame_time(self) -> float:
        return self._ingame_time

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.view_auras
    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def most_recent_game_obj(self) -> GameObj:
        return self._game_objs.most_recent_game_obj

    @property
    def important_ids(self) -> ImportantIDs:
        return self._game_objs.important_ids

    def aura_exists(self, u_event: UpcomingEvent) -> bool:
        return self._auras.aura_exists(u_event)

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        return self._auras.get_aura(source_id, spell_id, target_id)
    def get_game_obj(self, obj_id: int) -> GameObj:
        return self._game_objs.get_game_obj(obj_id)
    def get_spell(self, spell_id: int) -> Spell:
        return self._spell_database.get_spell(spell_id)

    def initialize_environment(self, setup_spell_id: int) -> None:
        self._game_objs.initialize_root_environment_obj(setup_spell_id)

    def advance_ingame_time(self, delta_time: float) -> None:
        self._ingame_time += delta_time

    def add_player_controls(self, player_input: Controls, timestamp: float) -> None:
        if timestamp != 0.0:
            self._controls.add_realtime_player_controls(self.important_ids.player_id, timestamp, player_input)

    def view_controls_for_current_frame(self, frame_start: float, frame_end: float) -> List[Tuple[float, int, Controls]]:
        assert frame_end == self._ingame_time
        return self._controls.get_controls_in_timerange(frame_start, frame_end)

    def let_event_modify_world_state(self, f_event: FinalizedEvent) -> None:
        if not f_event.outcome_is_valid:
            return
        if f_event.spell.has_spawned_object:
            new_obj = self._game_objs.handle_spawn(f_event.timestamp, f_event.target, f_event.spell)
            if new_obj is not None:
                self._controls.add_controls_for_newly_spawned_obj(new_obj, f_event.spell)
        if f_event.spell.has_aura_apply or f_event.spell.has_aura_cancel:
            self._auras.handle_aura(f_event)
        self._game_objs.modify_game_obj(f_event.timestamp, f_event.source, f_event.spell, f_event.target)
