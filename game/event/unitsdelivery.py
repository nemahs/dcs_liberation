import typing

from dcs.unittype import UnitType
from theater import ControlPoint
from . import Event


class UnitsDeliveryEvent(Event):
    informational: bool = True
    units: typing.Dict[UnitType, int] = None

    def __init__(self, attacker_name: str, defender_name: str, from_cp: ControlPoint, to_cp: ControlPoint, game):
        super(UnitsDeliveryEvent, self).__init__(game=game,
                                                 location=to_cp.position,
                                                 from_cp=from_cp,
                                                 target_cp=to_cp,
                                                 attacker_name=attacker_name,
                                                 defender_name=defender_name)

        self.units = {}

    def __str__(self) -> str:
        return "Pending delivery to {}".format(self.to_cp)

    def deliver(self, units: typing.Dict[UnitType, int]):
        for k, v in units.items():
            self.units[k] = self.units.get(k, 0) + v

    def skip(self):
        self.to_cp.base.commision_units(self.units)
