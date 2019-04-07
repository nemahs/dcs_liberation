import logging
import typing
from typing import Collection, Type
import random
import math

from dcs.task import *
from dcs.vehicles import *

from gen.conflictgen import Conflict
from userdata.debriefing import Debriefing
from theater import *

from . import db
from .settings import Settings
from .event import *

# TODO: Document these
COMMISION_UNIT_VARIETY = 4
COMMISION_LIMITS_SCALE = 1.5
COMMISION_LIMITS_FACTORS = {
    PinpointStrike: 10,
    CAS: 5,
    CAP: 8,
    AirDefence: 1,
}

COMMISION_AMOUNTS_SCALE = 1.5
COMMISION_AMOUNTS_FACTORS = {
    PinpointStrike: 3,
    CAS: 1,
    CAP: 2,
    AirDefence: 0.3,
}

PLAYER_INTERCEPT_GLOBAL_PROBABILITY_BASE = 30
PLAYER_INTERCEPT_GLOBAL_PROBABILITY_LOG = 2
PLAYER_BASEATTACK_THRESHOLD = 0.4

'''
Various events probabilities. First key is player probabilty, second is enemy probability.
For the enemy events, only 1 event of each type could be generated for a turn.

Events:
* BaseAttackEvent - capture base
* InterceptEvent - air intercept
* FrontlineAttackEvent - frontline attack
* NavalInterceptEvent - naval intercept
* StrikeEvent - strike event
* InfantryTransportEvent - helicopter infantry transport
'''
EVENT_PROBABILITIES = {
    # events always present; only for the player
    FrontlineAttackEvent: [100, 9],
    #FrontlinePatrolEvent: [100, 0],
    StrikeEvent: [100, 0],

    # events randomly present; only for the player
    #InfantryTransportEvent: [25, 0],
    ConvoyStrikeEvent: [25, 0],

    # events conditionally present; for both enemy and player
    BaseAttackEvent: [100, 9],

    # events randomly present; for both enemy and player
    InterceptEvent: [25, 9],
    NavalInterceptEvent: [25, 9],

    # events randomly present; only for the enemy
    InsurgentAttackEvent: [0, 6],
}

PLAYER_BASE_STRENGTH_RECOVERY: float = 0.2  # Amount of strength player bases recover for the turn.
ENEMY_BASE_STRENGTH_RECOVERY: float = 0.05  # Amount of strength enemy bases recover for the turn.
AWACS_BUDGET_COST: int = 4  # Cost of AWACS for single operation.
PLAYER_BUDGET_INITIAL: int = 170  # Initial budget value.
PLAYER_BUDGET_BASE: int = 14  # Base post-turn bonus value.
PLAYER_BUDGET_IMPORTANCE_LOG: int = 2  # Base post-turn bonus value.


class Game:
    settings: Settings = Settings()
    budget: int = PLAYER_BUDGET_INITIAL
    events: List[Event] = []
    ignored_cps: Collection[ControlPoint] = None

    def __init__(self, player_name: str, enemy_name: str, theater: ConflictTheater):
        """ Constructor

        :param player_name: Name of the player faction.
        :param enemy_name: Name of the enemy faction.
        :param theater: Theater of war for this game.
        """
        self.theater = theater
        self.player = player_name
        self.enemy = enemy_name

    def _roll(self, prob: int, mult: float) -> bool:
        """ Randomly determine if a given event occurs

        :param prob: Probability an event occurs.
        :param mult: Modifier to probability.
        :return: True if the event occurs, False otherwise.
        """
        if self.settings.version == "dev":
            # Always generate all events for development.
            return True
        else:
            return random.randint(1, 100) <= prob * mult

    def _generate_player_event(self, event_class: type, player_cp: ControlPoint, enemy_cp: ControlPoint):
        """ Generates a player event and adds it to the event list.

        :param event_class: Type of event to create.
        :param player_cp: CP the event will start from.
        :param enemy_cp: CP the event is targeting.
        """
        if event_class == NavalInterceptEvent and enemy_cp.radials == LAND:
            # Skip naval events for non-coastal CPs.
            return

        if event_class == BaseAttackEvent and \
                enemy_cp.base.strength > PLAYER_BASEATTACK_THRESHOLD and \
                self.settings.version != "dev":
            # Skip base attack events for CPs yet too strong.
            return

        if event_class == StrikeEvent and not enemy_cp.ground_objects:
            # Skip strikes in case of no targets.
            return

        self.events.append(event_class(self, player_cp, enemy_cp, enemy_cp.position, self.player, self.enemy))

    def _generate_enemy_event(self, event_class: Type[Event], player_cp: ControlPoint, enemy_cp: ControlPoint):
        """ Generates an enemy event and adds it to the event list.

        :param event_class: Type of event to generate.
        :param player_cp: Player CP to attack.
        :param enemy_cp: Enemy CP to start attack from.
        """
        if event_class in [type(x) for x in self.events if not self.is_player_attack(x)]:
            # Skip already generated enemy event types.
            return

        if player_cp in self.ignored_cps:
            # Skip attacks against ignored CPs (for example just captured ones).
            return

        if enemy_cp.base.total_planes == 0:
            # Skip event if there's no planes on the base.
            return

        if player_cp.is_global:
            # Skip carriers.
            return

        if event_class == NavalInterceptEvent:
            if player_cp.radials == LAND:
                # Skip naval events for non-coastal CPs.
                return
        elif event_class == StrikeEvent:
            if not player_cp.ground_objects:
                # Skip strikes if there's no ground objects.
                return
        elif event_class == BaseAttackEvent:
            if BaseAttackEvent in [type(x) for x in self.events]:
                # Skip base attack event if there's another one going on.
                return

            if enemy_cp.base.total_armor == 0:
                # Skip base attack if there's no armor.
                return

            if player_cp.base.strength > PLAYER_BASEATTACK_THRESHOLD:
                # Skip base attack if strength is too high.
                return

        self.events.append(event_class(self, enemy_cp, player_cp, player_cp.position, self.enemy, self.player))

    def _generate_events(self):
        """ Randomly generates events. TODO: Improve doc
        """
        strikes_generated_for = set()
        base_attack_generated_for = set()

        for player_cp, enemy_cp in self.theater.conflicts(True):
            for event_class, (player_probability, enemy_probability) in EVENT_PROBABILITIES.items():
                if event_class in [FrontlineAttackEvent, FrontlinePatrolEvent, InfantryTransportEvent, ConvoyStrikeEvent]:
                    # Skip events requiring frontline.
                    if not Conflict.has_frontline_between(player_cp, enemy_cp):
                        continue

                # Don't generate multiple 100% events from each attack direction.
                if event_class is StrikeEvent:
                    if enemy_cp in strikes_generated_for:
                        continue
                if event_class is BaseAttackEvent:
                    if enemy_cp in base_attack_generated_for:
                        continue

                if player_probability == 100 or (player_probability > 0 and self._roll(player_probability, player_cp.base.strength)):
                    self._generate_player_event(event_class, player_cp, enemy_cp)
                    if event_class is StrikeEvent:
                        strikes_generated_for.add(enemy_cp)
                    if event_class is BaseAttackEvent:
                        base_attack_generated_for.add(enemy_cp)

                if enemy_probability == 100 or enemy_probability > 0 and self._roll(enemy_probability, enemy_cp.base.strength):
                    self._generate_enemy_event(event_class, player_cp, enemy_cp)

    def commission_unit_types(self, cp: ControlPoint, for_task: Task) -> Collection[UnitType]:
        importance_factor = (cp.importance - IMPORTANCE_LOW) / (IMPORTANCE_HIGH - IMPORTANCE_LOW)

        if for_task == AirDefence and not self.settings.sams:
            return [x for x in db.find_unittype(AirDefence, self.enemy) if x not in db.SAM_BAN]
        else:
            return db.choose_units(for_task, importance_factor, COMMISION_UNIT_VARIETY, self.enemy)

    def _commission_units(self, cp: ControlPoint):
        for for_task in [PinpointStrike, CAS, CAP, AirDefence]:
            limit = COMMISION_LIMITS_FACTORS[for_task] * math.pow(cp.importance, COMMISION_LIMITS_SCALE) * self.settings.multiplier
            missing_units = limit - cp.base.total_units(for_task)
            if missing_units > 0:
                awarded_points = COMMISION_AMOUNTS_FACTORS[for_task] * math.pow(cp.importance, COMMISION_AMOUNTS_SCALE) * self.settings.multiplier
                points_to_spend = cp.base.append_commision_points(for_task, awarded_points)
                if points_to_spend > 0:
                    unittypes = self.commission_unit_types(cp, for_task)
                    d = {random.choice(unittypes): points_to_spend}
                    logging.info("Commission {}: {}".format(cp, d))
                    cp.base.commision_units(d)

    @property
    def budget_reward_amount(self) -> int:
        """ Determines how much money the player should be given each turn.

        :return: Amount (in millions of dollars) that the player will earn.
        """
        if len(self.theater.player_points()) > 0:
            total_importance = sum([x.importance * x.base.strength for x in self.theater.player_points()])
            return math.ceil(math.log(total_importance + 1, PLAYER_BUDGET_IMPORTANCE_LOG) * PLAYER_BUDGET_BASE * self.settings.multiplier)
        else:
            return 0

    def _budget_player(self):
        """ Give the player their income for the turn.
        """
        self.budget += self.budget_reward_amount

    def awacs_expense_commit(self):
        """ Deduct the cost of an AWACS from the player's budget.
        """
        self.budget -= AWACS_BUDGET_COST

    def units_delivery_event(self, to_cp: ControlPoint) -> UnitsDeliveryEvent:
        """ Creates a UnitsDeliveryEvent and adds it to the events list.

        :param to_cp: CP to deliver the units to.
        :return: Generated UnitsDeliveryEvent.
        """
        event = UnitsDeliveryEvent(attacker_name=self.player,
                                   defender_name=self.player,
                                   from_cp=to_cp,
                                   to_cp=to_cp,
                                   game=self)
        self.events.append(event)
        return event

    def units_delivery_remove(self, event: Event):
        """ Removes an event from the events list.

            QUESTION: Should this be restricted to UnitsDeliveryEvents or renamed to remove any event?
        :param event: Event to remove from the events list.
        """
        if event in self.events:
            self.events.remove(event)

    def initiate_event(self, event: Event):
        """ Generates a DCS mission for the event.

        :param event: Event to generate a mission for
        """
        assert event in self.events

        logging.info("Generating {} (regular)".format(event))
        event.generate()
        logging.info("Generating {} (quick)".format(event))
        event.generate_quick()

    def finish_event(self, event: Event, debriefing: Debriefing):
        """ Finishes an event after it has been flown.

        :param event: Event to complete.
        :param debriefing: Mission results from DCS.
        """
        logging.info("Finishing event {}".format(event))
        event.commit(debriefing)
        if event.is_successful(debriefing):
            self.budget += event.bonus()

        if event in self.events:
            self.events.remove(event)
        else:
            logging.info("finish_event: Event not in the events list!")

    def is_player_attack(self, event: Union[Country, Event]) -> bool:
        """ Determines if event is an event where the player is attacking.
            QUESTION: Should this be split into two seperate functions?
        :param event: Country or Event to check
        :return: True if event is an event where the player is attacking, False otherwise.
        """
        if isinstance(event, Event):
            return event.attacker_name == self.player
        else:
            return event.name == self.player

    def pass_turn(self, no_action: bool = False, ignored_cps: Collection[ControlPoint] = None):
        """ End player and start a new turn.

        :param no_action: If True, do no actions this turn.
        :param ignored_cps: Collection of CPs to ignore in the next turn.
        """
        logging.info("Pass turn")
        for event in self.events:
            if self.settings.version == "dev":
                # Don't damage player CPs in by skipping in dev mode.
                if isinstance(event, UnitsDeliveryEvent):
                    event.skip()
            else:
                event.skip()

        if not no_action:
            self._budget_player()

            for cp in self.theater.enemy_points():
                self._commission_units(cp)

            for cp in self.theater.player_points():
                cp.base.affect_strength(+PLAYER_BASE_STRENGTH_RECOVERY)

        self.ignored_cps = []
        if ignored_cps:
            self.ignored_cps = ignored_cps

        self.events: List[Event] = []
        self._generate_events()
        # self._generate_globalinterceptions()

