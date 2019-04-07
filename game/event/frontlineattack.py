import math
from typing import Collection, Type

from .event import Event
from game import db
from game.operation.frontlineattack import FrontlineAttackOperation
from userdata.debriefing import Debriefing
from dcs.task import MainTask, CAS, CAP, PinpointStrike


class FrontlineAttackEvent(Event):
    TARGET_VARIETY = 2
    TARGET_AMOUNT_FACTOR = 0.5
    ATTACKER_AMOUNT_FACTOR = 0.4
    ATTACKER_DEFENDER_FACTOR = 0.7
    STRENGTH_INFLUENCE = 0.3
    SUCCESS_FACTOR = 1.5

    @property
    def threat_description(self):
        return "{} vehicles".format(self.to_cp.base.assemble_count())

    @property
    def tasks(self) -> Collection[Type[MainTask]]:
        if self.is_player_attacking:
            return [CAS, CAP]
        else:
            return [CAP]

    @property
    def global_cp_available(self) -> bool:
        return True

    def flight_name(self, for_task: Type[MainTask]) -> str:
        if for_task == CAS:
            return "CAS flight"
        elif for_task == CAP:
            return "CAP flight"
        elif for_task == PinpointStrike:
            return "Ground attack"

    def __str__(self):
        return "Frontline attack"

    def is_successful(self, debriefing: Debriefing):
        alive_attackers = sum([v for k, v in debriefing.alive_units.get(self.attacker_name, {}).items() if db.unit_task(k) == PinpointStrike])
        alive_defenders = sum([v for k, v in debriefing.alive_units.get(self.defender_name, {}).items() if db.unit_task(k) == PinpointStrike])
        attackers_success = (float(alive_attackers) / (alive_defenders + 0.01)) > self.SUCCESS_FACTOR
        if self.from_cp.captured:
            return attackers_success
        else:
            return not attackers_success

    def commit(self, debriefing: Debriefing):
        super(FrontlineAttackEvent, self).commit(debriefing)

        if self.from_cp.captured:
            if self.is_successful(debriefing):
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.to_cp.base.affect_strength(+self.STRENGTH_INFLUENCE)
        else:
            if self.is_successful(debriefing):
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def skip(self):
        if self.to_cp.captured:
            self.to_cp.base.affect_strength(-0.1)

    def player_attacking(self, flights: db.TaskForceDict):
        assert CAS in flights and CAP in flights and len(flights) == 2, "Invalid flights"

        op = FrontlineAttackOperation(game=self.game,
                                      attacker_name=self.attacker_name,
                                      defender_name=self.defender_name,
                                      from_cp=self.from_cp,
                                      departure_cp=self.departure_cp,
                                      to_cp=self.to_cp)

        defenders = self.to_cp.base.assemble_attack()
        max_attackers = int(math.ceil(sum(defenders.values()) * self.ATTACKER_DEFENDER_FACTOR))
        attackers = db.unitdict_restrict_count(self.from_cp.base.assemble_attack(), max_attackers)
        op.setup(defenders=defenders,
                 attackers=attackers,
                 strikegroup=flights[CAS],
                 escort=flights[CAP],
                 interceptors=db.assigned_units_from(self.to_cp.base.scramble_interceptors(1)))

        self.operation = op

    def player_defending(self, flights: db.TaskForceDict):
        assert CAP in flights and len(flights) == 1, "Invalid flights"

        op = FrontlineAttackOperation(game=self.game,
                                      attacker_name=self.attacker_name,
                                      defender_name=self.defender_name,
                                      from_cp=self.from_cp,
                                      departure_cp=self.departure_cp,
                                      to_cp=self.to_cp)

        defenders = self.to_cp.base.assemble_attack()

        max_attackers = int(math.ceil(sum(defenders.values())))
        attackers = db.unitdict_restrict_count(self.from_cp.base.assemble_attack(), max_attackers)

        op.setup(defenders=defenders,
                 attackers=attackers,
                 strikegroup=db.assigned_units_from(self.from_cp.base.scramble_cas(1)),
                 escort=db.assigned_units_from(self.from_cp.base.scramble_sweep(1)),
                 interceptors=flights[CAP])

        self.operation = op

