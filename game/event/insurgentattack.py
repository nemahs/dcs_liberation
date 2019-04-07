import math
import random
from typing import Type, List, Dict

from dcs.task import MainTask, PinpointStrike, CAS, Reconnaissance
from dcs.unittype import VehicleType
from game import db
from game.operation.insurgentattack import InsurgentAttackOperation
from userdata.debriefing import Debriefing
from .event import Event


class InsurgentAttackEvent(Event):
    SUCCESS_FACTOR: float = 0.7
    TARGET_VARIETY: int = 2
    TARGET_AMOUNT_FACTOR: float = 0.5
    STRENGTH_INFLUENCE: float = 0.1

    targets: Dict[VehicleType, int] = None

    @property
    def threat_description(self) -> str:
        return ""

    @property
    def tasks(self) -> List[Type[MainTask]]:
        return [CAS]

    def flight_name(self, for_task: Type[MainTask]) -> str:
        if for_task == CAS:
            return "Ground intercept flight"

    def __str__(self) -> str:
        return "Destroy insurgents"

    def skip(self):
        self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def is_successful(self, debriefing: Debriefing) -> bool:
        killed_units = sum([v for k, v in debriefing.destroyed_units[self.attacker_name].items() if db.unit_task(k) == PinpointStrike])
        all_units = sum(self.targets.values())
        attackers_success = (float(killed_units) / (all_units + 0.01)) > self.SUCCESS_FACTOR
        if self.from_cp.captured:
            return attackers_success
        else:
            return not attackers_success

    def player_defending(self, flights: db.TaskForceDict):
        assert CAS in flights and len(flights) == 1, "Invalid flights"

        suitable_unittypes = db.find_unittype(Reconnaissance, self.attacker_name)
        random.shuffle(suitable_unittypes)
        unittypes = suitable_unittypes[:self.TARGET_VARIETY]
        typecount = max(math.floor(self.difficulty * self.TARGET_AMOUNT_FACTOR), 1)
        self.targets = {unittype: typecount for unittype in unittypes}

        op = InsurgentAttackOperation(game=self.game,
                                      attacker_name=self.attacker_name,
                                      defender_name=self.defender_name,
                                      from_cp=self.from_cp,
                                      departure_cp=self.departure_cp,
                                      to_cp=self.to_cp)
        op.setup(target=self.targets,
                 strikegroup=flights[CAS])

        self.operation = op
