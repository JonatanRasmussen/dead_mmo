from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.aura import Aura
from src.models.combat_event import CombatEvent, FinalizedEvent
from src.handlers.aura_handler import AuraHandler
from src.handlers.controls_handler import ControlsHandler
from src.handlers.game_obj_handler import GameObjHandler
from src.handlers.event_heap import EventHeap
from src.handlers.event_log import EventLog
from src.config.spell_db import SpellDatabase
from src.utils.spell_handler import SpellHandler
from src.utils.spell_validator import SpellValidator


class ReadOnlyWorldState:
    def __init__(self,
        event_id_gen: IdGen,
        prev_t: float,
        curr_t: float,
        auras: AuraHandler,
        controls: ControlsHandler,
        game_objs: GameObjHandler,
        spell_database: SpellDatabase,
        event_log: EventLog,
    ) -> None:
        self.event_id_gen: IdGen = event_id_gen

        self.prev_t: float = prev_t
        self.curr_t: float = curr_t

        self.auras: AuraHandler = auras
        self.controls: ControlsHandler = controls
        self.game_objs: GameObjHandler = game_objs
        self.spell_database: SpellDatabase = spell_database
        self.event_log: EventLog = event_log