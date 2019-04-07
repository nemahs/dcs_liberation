import math
import random
from typing import Type, Tuple, List

from dcs.task import MainTask, CAS, Reconnaissance, PinpointStrike

from game import db
from userdata.debriefing import Debriefing
from .event import Event
from game.operation.convoystrike import ConvoyStrikeOperation

TRANSPORT_COUNT: Tuple[int, int] = (4, 6)
DEFENDERS_AMOUNT_FACTOR: int = 4


class ConvoyStrikeEvent(Event):
    SUCCESS_FACTOR: float = 0.6
    STRENGTH_INFLUENCE: float = 0.25

    targets: db.ArmorDict = None

    @property
    def threat_description(self) -> str:
        return ""

    @property
    def tasks(self) -> List[Type[MainTask]]:
        return [CAS]

    @property
    def global_cp_available(self) -> bool:
        return True

    def flight_name(self, for_task: Type[MainTask]) -> str:
        if for_task == CAS:
            return "Strike flight"

    def __str__(self) -> str:
        return "Convoy Strike"

    def skip(self):
        self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def commit(self, debriefing: Debriefing):
        super(ConvoyStrikeEvent, self).commit(debriefing)

        if self.from_cp.captured:
            if self.is_successful(debriefing):
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
        else:
            if self.is_successful(debriefing):
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def is_successful(self, debriefing: Debriefing) -> bool:
        killed_units = sum([v for k, v in debriefing.destroyed_units.get(self.defender_name, {}).items() if db.unit_task(k) in [PinpointStrike, Reconnaissance]])
        all_units = sum(self.targets.values())
        attackers_success = (float(killed_units) / (all_units + 0.01)) > self.SUCCESS_FACTOR
        if self.from_cp.captured:
            return attackers_success
        else:
            return not attackers_success

    def player_attacking(self, flights: db.TaskForceDict):
        assert CAS in flights and len(flights) == 1, "Invalid flights"

        convoy_unittype = db.find_unittype(Reconnaissance, self.defender_name)[0]
        defense_unittype = db.find_unittype(PinpointStrike, self.defender_name)[0]

        defenders_count = int(math.ceil(self.from_cp.base.strength * self.from_cp.importance * DEFENDERS_AMOUNT_FACTOR))
        self.targets = {convoy_unittype: random.randrange(*TRANSPORT_COUNT),
                        defense_unittype: defenders_count, }

        op = ConvoyStrikeOperation(game=self.game,
                                   attacker_name=self.attacker_name,
                                   defender_name=self.defender_name,
                                   from_cp=self.from_cp,
                                   departure_cp=self.departure_cp,
                                   to_cp=self.to_cp)
        op.setup(target=self.targets,
                 strikegroup=flights[CAS])

        self.operation = op
