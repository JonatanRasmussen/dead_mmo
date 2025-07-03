from enum import Enum, auto

class Hostility(Enum):
    """ Team relationships between GameObjs, used for spell targeting. """
    EMPTY = 0
    ALLIED = auto()
    ENEMY = auto()
    NEUTRAL = auto()

    @property
    def is_allied(self) -> bool:
        return self in {Hostility.ALLIED}

    @property
    def is_enemy(self) -> bool:
        return self in {Hostility.ENEMY}

    def is_valid_aoe_target(self, sources_team: 'Hostility', targets_team: 'Hostility') -> bool:
        return (self == sources_team) == (sources_team == targets_team)

    def decide_team_based_on_parent(self, parents_team: 'Hostility') -> 'Hostility':
        if parents_team in {Hostility.NEUTRAL}:
            return self
        return parents_team