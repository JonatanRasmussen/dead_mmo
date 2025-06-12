from typing import List, Tuple, Iterable, ValuesView, Optional

from src.models import Aura, Controls, GameObj, ImportantIDs, UpcomingEvent, FinalizedEvent, Spell
from src.handlers import AuraHandler, ControlsHandler, GameObjHandler, SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._auras: AuraHandler = AuraHandler()
        self._controls: ControlsHandler = ControlsHandler()
        self._game_objs: GameObjHandler = GameObjHandler()

        self._spell_database: SpellDatabase = SpellDatabase()

    @property
    def view_auras(self) -> ValuesView[Aura]:
        return self._auras.view_auras
    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def important_ids(self) -> ImportantIDs:
        return self._game_objs.important_ids

    def aura_exists(self, u_event: UpcomingEvent) -> bool:
        return self._auras.aura_exists(u_event)
    def get_obj_auras(self, obj_id: int) -> Iterable[Aura]:
        yield from self._auras.get_obj_auras(obj_id)
    def remove_all_expired_auras(self, frame_end: float) -> None:
        cached_source: GameObj = GameObj()
        for aura in self.view_auras:
            if aura.source_id != cached_source.obj_id:
                # Because view_auras is a SortedDict, auras from the same source is in sequence
                assert aura.source_id > cached_source.obj_id
                cached_source = self.get_game_obj(aura.source_id)
            if aura.is_expired(frame_end) or cached_source.is_despawned:
                self._auras.remove_aura(*aura.get_key_for_aura)

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        return self._auras.get_aura(source_id, spell_id, target_id)
    def get_game_obj(self, obj_id: int) -> GameObj:
        return self._game_objs.get_game_obj(obj_id)
    def get_spell(self, spell_id: int) -> Spell:
        return self._spell_database.get_spell(spell_id)

    def initialize_environment(self, setup_spell_id: int) -> None:
        self._game_objs.initialize_root_environment_obj(setup_spell_id)

    def add_realtime_player_controls(self, player_input: Controls, frame_middle: float) -> None:
        if frame_middle != 0.0:
            self._controls.add_realtime_player_controls(self.important_ids.player_id, frame_middle, player_input)

    def view_controls_for_current_frame(self, frame_start: float, frame_end: float) -> Iterable[Tuple[float, int, Controls]]:
        yield from self._controls.get_controls_in_timerange(frame_start, frame_end)

    def let_event_spawn_new_obj(self, f_event: FinalizedEvent) -> Optional[GameObj]:
        if f_event.spell.has_spawned_object:
            new_obj = self._game_objs.handle_spawn(f_event.timestamp, f_event.target, f_event.spell)
            if new_obj is not None:
                self._controls.add_controls_for_newly_spawned_obj(new_obj, f_event.spell)
            return new_obj
        return None

    def let_event_modify_aura(self, f_event: FinalizedEvent) -> None:
        if f_event.spell.has_aura_apply or f_event.spell.has_aura_cancel:
            self._auras.handle_aura(f_event)

    def let_event_modify_game_obj(self, f_event: FinalizedEvent) -> None:
        self._game_objs.modify_game_obj(f_event.timestamp, f_event.source, f_event.spell, f_event.target)
