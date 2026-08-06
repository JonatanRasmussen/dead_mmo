from typing import Iterable
from dataclasses import dataclass
from ._controls_data import Controls, InputTranslator, KeyPresses, Loadout
from ._spell_database import SpellDatabase


@dataclass(slots=True)
class SpellControlsData:
    """Stores only the movement-relevant data extracted from a Spell."""
    loadout: Loadout
    controls: tuple[Controls, ...]


class ControlsSystem:
    def __init__(self, spell_database: SpellDatabase) -> None:
        # Map spell_id -> template controls data
        self._templates: dict[int, SpellControlsData] = ControlsSystem._create_initialized_spell_data_dct(spell_database)
        # Map runtime obj_id -> active controls data
        self._active_controls: dict[int, SpellControlsData] = {}

    @staticmethod
    def _create_initialized_spell_data_dct(spell_database: SpellDatabase) -> dict[int, SpellControlsData]:
        templates = {}
        for spell in spell_database.get_all_spells():
            if spell.spawned_obj is not None:
                game_obj = spell.spawned_obj.game_obj
                controls_tuple = spell.spawned_obj.obj_controls or ()
                templates[spell.spell_id] = SpellControlsData(
                    loadout=game_obj._loadout,
                    controls=controls_tuple
                )
        return templates

    def spawn_game_obj(self, obj_id: int, spell_id: int) -> None:
        """Called by WorldState when a new object is spawned to register its controls."""
        if spell_id in self._templates:
            self._active_controls[obj_id] = self._templates[spell_id]

    def get_spell_ids_for_inputs(self, obj_id: int, hardware_inputs: list[str], timestamp: int) -> Iterable[int]:
        if not hardware_inputs:
            yield from []
            return
        key_presses = InputTranslator.translate_to_keypresses(hardware_inputs)
        if key_presses == KeyPresses.NONE:
            yield from []
            return
        controls_data = self._active_controls.get(obj_id)
        if not controls_data:
            yield from []
        else:
            controls = Controls(obj_id=obj_id, timeline_timestamp=timestamp, key_presses=key_presses)
            yield from controls_data.loadout.convert_controls_to_spell_ids(controls, obj_id)

    def get_scripted_spells(self, obj_id: int, spawn_timestamp: int) -> Iterable[tuple[int, int, int]]:
        controls_data = self._active_controls.get(obj_id)
        if not controls_data or not controls_data.controls:
            return

        for original_controls in controls_data.controls:
            # Create a copy and apply the offset, just like the old system
            controls = original_controls.create_copy()
            controls.increase_offset(spawn_timestamp)

            priority = 0
            for spell_id in controls_data.loadout.convert_controls_to_spell_ids(controls, obj_id):
                priority += 1
                yield spell_id, controls.ingame_time, priority