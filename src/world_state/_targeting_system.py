from src.settings import Consts
from src.world_state import Targeting
from ._combat_system import CombatSystem
from ._obj_registry import ObjRegistry
from ._spell_meta_system import SpellMetaSystem


class TargetingSystem:
    """ID-only replacement of WorldState._decide_targeting() (no GameObj, no Spell)."""

    def __init__(self, spell_meta: SpellMetaSystem, combat: CombatSystem, registry: ObjRegistry) -> None:
        self._meta = spell_meta
        self._combat = combat
        self._registry = registry

    def resolve_target_id(self, spell_id: int, source_id: int,
                          predetermined_target_id: int, is_aoe_targeting: bool) -> int:
        targeting = self._meta.get_targeting(spell_id)
        assert targeting is not Targeting.NONE, \
            f"obj {source_id} is casting spell {spell_id} with targeting=NONE"

        ids = self._registry.default_ids
        current_target = self._combat.get_current_target(source_id)
        parent_id = self._registry.get_parent_id(source_id)
        source_is_allied = self._combat.is_on_players_team(source_id)

        if targeting in (Targeting.SELF, Targeting.DEFAULT_FRIENDLY):
            target_id = source_id
        elif targeting in (Targeting.TARGET, Targeting.TARGET_OF_TARGET) and Consts.is_valid_id(current_target):
            target_id = current_target
        elif targeting in (Targeting.PARENT, Targeting.TARGET_OF_PARENT) and Consts.is_valid_id(parent_id):
            target_id = parent_id
        elif targeting is Targeting.DEFAULT_ENEMY:
            target_id = ids.boss1_id if source_is_allied else ids.player_id
        elif targeting is Targeting.TAB_TO_NEXT:
            if not source_is_allied:
                target_id = ids.player_id
            elif current_target == ids.boss1_id and ids.boss2_exists:
                target_id = ids.boss2_id
            elif Consts.is_valid_id(ids.boss1_id):
                target_id = ids.boss1_id
            else:
                target_id = ids.player_id  # not implemented: assume boss1 exists
        else:
            target_id = ids.missing_target_id

        # Indirect targeting: copy the target of the resolved object
        if targeting in (Targeting.TARGET_OF_TARGET, Targeting.TARGET_OF_PARENT) and Consts.is_valid_id(target_id):
            relayed = self._combat.get_current_target(target_id)
            target_id = relayed if Consts.is_valid_id(relayed) else ids.missing_target_id

        # AoE splash targets are predetermined by the parent event
        if is_aoe_targeting:
            target_id = predetermined_target_id

        return target_id