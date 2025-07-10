from enum import Enum, auto

class Faction(Enum):
    """ Team relationships between GameObjs, used for spell targeting. """
    EMPTY = 0
    ALLIED = auto()
    ENEMY = auto()
    NEUTRAL = auto()

    @property
    def is_allied(self) -> bool:
        return self in {Faction.ALLIED}

    @property
    def is_enemy(self) -> bool:
        return self in {Faction.ENEMY}

    def is_valid_aoe_target(self, sources_team: 'Faction', targets_team: 'Faction') -> bool:
        return (self == sources_team) == (sources_team == targets_team)

    def decide_team_based_on_parent(self, parents_team: 'Faction') -> 'Faction':
        if parents_team in {Faction.NEUTRAL}:
            return self
        return parents_team