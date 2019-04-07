import logging

from dcs.unittype import UnitType
from dcs.task import *
from dcs.vehicles import AirDefence
from dcs.unittype import UnitType

from game.operation.operation import Operation
from theater import *
from gen.environmentgen import EnvironmentSettings
from gen.conflictgen import Conflict
from game.db import assigned_units_from, unitdict_from

from userdata.debriefing import Debriefing
from userdata import persistency

DIFFICULTY_LOG_BASE: float = 1.1
EVENT_DEPARTURE_MAX_DISTANCE: int = 340000


class Event:
    """ Base class for Events.
    QUESTION: Can this be made abstract?
    """
    silent: bool = False
    informational: bool = False
    is_awacs_enabled: bool = False
    ca_slots: int = 0

    game = None
    location: Point = None
    from_cp: ControlPoint = None
    departure_cp: ControlPoint = None
    to_cp: ControlPoint = None

    operation: Operation = None
    difficulty: int = 1
    environment_settings: EnvironmentSettings = None
    BONUS_BASE: int = 5

    def __init__(self, game, from_cp: ControlPoint, target_cp: ControlPoint, location: Point, attacker_name: str, defender_name: str):
        """ Constructor.

        :param game: Game this event belongs to.
        :param from_cp: CP this event originates from.
        :param target_cp: CP this event is targeting.
        :param location: Location of mission operations.
        :param attacker_name: Name of attacking faction.
        :param defender_name: Name of defending faction.
        """
        self.game = game
        self.departure_cp = None
        self.from_cp = from_cp
        self.to_cp = target_cp
        self.location = location
        self.attacker_name = attacker_name
        self.defender_name = defender_name

    @property
    def is_player_attacking(self) -> bool:
        """ Determines if the player is attacking in this event.

            QUESTION: Is having this AND game.is_player_attack redundant?
        :return: True if the player is attacking in this event.
        """
        return self.attacker_name == self.game.player

    @property
    def enemy_cp(self) -> ControlPoint:
        """ Returns the CP that belongs to the enemy.

        :return: CP belonging to the enemy.
        """
        if self.attacker_name == self.game.player:
            return self.to_cp
        else:
            return self.departure_cp

    @property
    def threat_description(self) -> str:
        return ""

    def flight_name(self, for_task: typing.Type[typing.Type[Task]]) -> str:
        return "Flight"

    @property
    def tasks(self) -> typing.Collection[typing.Type[Task]]:
        return []

    @property
    def ai_banned_tasks(self) -> typing.Collection[typing.Type[Task]]:
        return []

    @property
    def player_banned_tasks(self) -> typing.Collection[typing.Type[Task]]:
        return []

    @property
    def global_cp_available(self) -> bool:
        return False

    def is_departure_available_from(self, cp: ControlPoint) -> bool:
        """ Determines if a departure is available from the given control point

        :param cp: Control point to see if departure is available from.
        :return: True if we can depart from the given CP, False otherwise.
        """
        if not cp.captured:
            return False

        if self.location.distance_to_point(cp.position) > EVENT_DEPARTURE_MAX_DISTANCE:
            return False

        if cp.is_global and not self.global_cp_available:
            return False

        return True

    def bonus(self) -> int:
        return int(math.log(self.to_cp.importance + 1, DIFFICULTY_LOG_BASE) * self.BONUS_BASE)

    def is_successful(self, debriefing: Debriefing) -> bool:
        return self.operation.is_successful(debriefing)

    def player_attacking(self, cp: ControlPoint, flights: db.TaskForceDict):
        """ Sets the event such that the player is attacking or the player is leaving from on an attack.
            NOTE: This function does multiple things, it needs to be refactored.

        :param cp: CP to depart from is the player is attacking, else the CP to head to.
        :param flights: Not used.
        """
        if self.is_player_attacking:
            self.departure_cp = cp
        else:
            self.to_cp = cp

    def player_defending(self, cp: ControlPoint, flights: db.TaskForceDict):
        """ Sets the event such that the player is attacking or the player is leaving from on an attack.
            NOTE: This is identical to player_attacking.

        :param cp: CP to depart from is the player is attacking, else the CP to head to.
        :param flights: Not used.
        """
        if self.is_player_attacking:
            self.departure_cp = cp
        else:
            self.to_cp = cp

    def generate(self):
        """ Generates a mission for this event.
        """
        self.operation.is_awacs_enabled = self.is_awacs_enabled
        self.operation.ca_slots = self.ca_slots

        self.operation.prepare(self.game.theater.terrain, is_quick=False)
        self.operation.generate()
        self.operation.current_mission.save(persistency.mission_path_for("liberation_nextturn.miz"))
        self.environment_settings = self.operation.environment_settings

    def generate_quick(self):
        """ Generates a quick mission for this event.
            QUESTION: Can this be combined with the previous function?
        """
        self.operation.is_awacs_enabled = self.is_awacs_enabled
        self.operation.environment_settings = self.environment_settings

        self.operation.prepare(self.game.theater.terrain, is_quick=True)
        self.operation.generate()
        self.operation.current_mission.save(persistency.mission_path_for("liberation_nextturn_quick.miz"))

    def commit(self, debriefing: Debriefing):
        """ Processes debriefing and commits losses to the CPs involved.

        :param debriefing: Debriefing to process.
        """
        for country, losses in debriefing.destroyed_units.items():
            if country == self.attacker_name:
                cp = self.departure_cp
            else:
                cp = self.to_cp

            logging.info("base {} commit losses {}".format(cp.base, losses))
            cp.base.commit_losses(losses)

        for object_identifier in debriefing.destroyed_objects:
            for cp in self.game.theater.controlpoints:
                if not cp.ground_objects:
                    continue

                for i, ground_object in enumerate(cp.ground_objects):
                    if ground_object.is_dead:
                        continue

                    if ground_object.matches_string_identifier(object_identifier):
                        logging.info("CP {} killing ground object {}".format(cp, ground_object.string_identifier))
                        cp.ground_objects[i].is_dead = True

    def skip(self):
        """ TODO: Implement me!
        """
        pass
