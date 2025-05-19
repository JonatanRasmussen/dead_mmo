from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.important_ids import ImportantIDs
from src.models.spell import SpellFlag, Spell
from src.models.aura import Aura
from src.models.combat_event import CombatEvent, FinalizedEvent
from src.handlers.aura_handler import AuraHandler
from src.handlers.controls_handler import ControlsHandler
from src.handlers.game_obj_handler import GameObjHandler
from src.handlers.event_log import EventLog
from src.handlers.spell_database import SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self._previous_timestamp: float = 0.0
        self._current_timestamp: float = 0.0

        self._auras: AuraHandler = AuraHandler()
        self._controls: ControlsHandler = ControlsHandler()
        self._game_objs: GameObjHandler = GameObjHandler()

        self._spell_database: SpellDatabase = SpellDatabase()
        self._event_log: EventLog = EventLog()

    @property
    def timestamps(self) -> Tuple[float,float]:
        return (self._previous_timestamp, self._current_timestamp)
    @property
    def delta_time(self) -> float:
        return self._current_timestamp - self._previous_timestamp

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.view_auras
    @property
    def view_controls_for_current_frame(self) -> List[Tuple[float, int, Controls]]:
        prev_t, curr_t = self._previous_timestamp, self._current_timestamp
        min_id, max_id = self._game_objs.get_lowest_and_highest_game_obj_id
        return self._controls.get_controls_in_timerange(prev_t, curr_t, min_id, max_id)
    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def important_ids(self) -> ImportantIDs:
        return self._game_objs.important_ids

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        return self._auras.get_aura(source_id, spell_id, target_id)
    def get_game_obj(self, obj_id: int) -> GameObj:
        return self._game_objs.get_game_obj(obj_id)
    def get_spell(self, spell_id: int) -> Spell:
        return self._spell_database.get_spell(spell_id)

    def generate_new_event_id(self) -> int:
        return self._event_id_gen.generate_new_id()

    def initialize_environment(self, setup_spell_id: int) -> None:
        self._game_objs.initialize_root_environment_obj(setup_spell_id)

    def advance_timestamp_and_add_player_input(self, delta_time: float, player_input: Controls) -> None:
        self._previous_timestamp = self._current_timestamp
        self._current_timestamp += delta_time
        self._controls.add_realtime_player_controls(self.important_ids.player_id, self._current_timestamp, player_input)

    def let_event_modify_world_state(self, f_event: FinalizedEvent) -> None:
        if not f_event.outcome_is_valid:
            return
        self._event_log.log_event(f_event.combat_event)
        spell = f_event.spell
        if spell.has_spawned_object:
            new_obj_id = self._game_objs.handle_spawn(f_event.source, spell)
            self._controls.try_add_controls_for_newly_spawned_obj(new_obj_id, spell)
        if spell.has_aura_apply or spell.has_aura_cancel:
            self._auras.handle_aura(f_event.timestamp, f_event.source_id, spell, f_event.target_id)
        self._game_objs.modify_game_obj(f_event.timestamp, f_event.source, spell, f_event.target)