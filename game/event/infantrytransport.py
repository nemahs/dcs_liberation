from typing import List, Type

from dcs.task import Task, Embarking
from dcs.vehicles import AirDefence

from game import db
from game.operation.infantrytransport import InfantryTransportOperation
from userdata.debriefing import Debriefing

from .event import Event


class InfantryTransportEvent(Event):
    STRENGTH_INFLUENCE: float = 0.3

    def __str__(self) -> str:
        return "Frontline transport troops"

    @property
    def tasks(self) -> List[Type[Task]]:
        return [Embarking]

    def flight_name(self, for_task: Type[Task]) -> str:
        if for_task == Embarking:
            return "Transport flight"

    def is_successful(self, debriefing: Debriefing):
        return True

    def commit(self, debriefing: Debriefing):
        super(InfantryTransportEvent, self).commit(debriefing)

        if self.is_successful(debriefing):
            self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
        else:
            self.departure_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def player_attacking(self, flights: db.TaskForceDict):
        assert Embarking in flights and len(flights) == 1, "Invalid flights"

        op = InfantryTransportOperation(
            game=self.game,
            attacker_name=self.attacker_name,
            defender_name=self.defender_name,
            from_cp=self.from_cp,
            departure_cp=self.departure_cp,
            to_cp=self.to_cp
        )

        air_defense = db.find_unittype(AirDefence, self.defender_name)[0]
        op.setup(transport=flights[Embarking],
                 aa={air_defense: 2})

        self.operation = op
