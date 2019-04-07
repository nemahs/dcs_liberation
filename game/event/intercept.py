import random
from typing import Type, List

from game import db
from theater import ControlPoint, Point
from gen.conflictgen import Conflict
from dcs.planes import FlyingType
from dcs.vehicles import AirDefence
from dcs.task import CAP, Transport, MainTask
from game.operation.intercept import InterceptOperation
from .event import Event
from userdata.debriefing import Debriefing


class InterceptEvent(Event):
    STRENGTH_INFLUENCE: float = 0.3
    GLOBAL_STRENGTH_INFLUENCE: float = 0.3
    AIRDEFENSE_COUNT: int = 3

    transport_unit: FlyingType = None

    def __init__(self, game, from_cp: ControlPoint, target_cp: ControlPoint, location: Point, attacker_name: str,
                 defender_name: str):
        super().__init__(game, from_cp, target_cp, location, attacker_name, defender_name)
        self.location = Conflict.intercept_position(self.from_cp, self.to_cp)

    def __str__(self) -> str:
        return "Air Intercept"

    @property
    def tasks(self) -> List[Type[MainTask]]:
        return [CAP]

    def flight_name(self, for_task: Type[MainTask]) -> str:
        if for_task == CAP:
            if self.is_player_attacking:
                return "Intercept flight"
            else:
                return "Escort flight"

    def _enemy_scramble_multiplier(self) -> float:
        is_global = self.departure_cp.is_global or self.to_cp.is_global
        return self.game.settings.multiplier * is_global and 0.5 or 1

    @property
    def threat_description(self) -> str:
        return "{} aircraft".format(self.enemy_cp.base.scramble_count(self._enemy_scramble_multiplier(), CAP))

    @property
    def global_cp_available(self) -> bool:
        return True

    def is_successful(self, debriefing: Debriefing):
        units_destroyed = debriefing.destroyed_units.get(self.defender_name, {}).get(self.transport_unit, 0)
        if self.from_cp.captured:
            return units_destroyed > 0
        else:
            return units_destroyed == 0

    def commit(self, debriefing: Debriefing):
        super(InterceptEvent, self).commit(debriefing)

        if self.attacker_name == self.game.player:
            if self.is_successful(debriefing):
                for _, cp in self.game.theater.conflicts(True):
                    cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
        else:
            # enemy attacking
            if self.is_successful(debriefing):
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def skip(self):
        if self.to_cp.captured:
            self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def player_attacking(self, flights: db.TaskForceDict):
        assert CAP in flights and len(flights) == 1, "Invalid flights"

        escort = self.to_cp.base.scramble_sweep(self._enemy_scramble_multiplier())

        self.transport_unit = random.choice(db.find_unittype(Transport, self.defender_name))
        assert self.transport_unit is not None

        airdefense_unit = db.find_unittype(AirDefence, self.defender_name)[-1]
        op = InterceptOperation(game=self.game,
                                attacker_name=self.attacker_name,
                                defender_name=self.defender_name,
                                from_cp=self.from_cp,
                                departure_cp=self.departure_cp,
                                to_cp=self.to_cp)

        op.setup(location=self.location,
                 escort=db.assigned_units_from(escort),
                 transport={self.transport_unit: 1},
                 airdefense={airdefense_unit: self.AIRDEFENSE_COUNT},
                 interceptors=flights[CAP])

        self.operation = op

    def player_defending(self, flights: db.TaskForceDict):
        assert CAP in flights and len(flights) == 1, "Invalid flights"

        interceptors = self.from_cp.base.scramble_interceptors(self.game.settings.multiplier)

        self.transport_unit = random.choice(db.find_unittype(Transport, self.defender_name))
        assert self.transport_unit is not None

        op = InterceptOperation(game=self.game,
                                attacker_name=self.attacker_name,
                                defender_name=self.defender_name,
                                from_cp=self.from_cp,
                                departure_cp=self.departure_cp,
                                to_cp=self.to_cp)

        op.setup(location=self.location,
                 escort=flights[CAP],
                 transport={self.transport_unit: 1},
                 interceptors=db.assigned_units_from(interceptors),
                 airdefense={})

        self.operation = op


