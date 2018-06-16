import typing

from dcs.vehicles import *
from dcs.unitgroup import *
from dcs.ships import *
from dcs.planes import *
from dcs.task import *
from dcs.unittype import *

PRICES = {
    # fighter
    C_101CC: 10,
    AJS37: 15,
    F_5E: 12,
    MiG_23MLD: 15,
    MiG_25PD: 20,
    MiG_31: 30,
    Su_27: 30,
    Su_33: 33,
    MiG_15bis: 8,
    MiG_21Bis: 13,
    MiG_29A: 23,
    FA_18C_hornet: 18,
    AV8BNA: 15,
    F_15C: 30,
    M_2000C: 15,

    # bomber
    Su_25T: 15,
    Su_24M: 18,
    Su_17M4: 13,
    L_39ZA: 10,
    MiG_29G: 18,
    Su_34: 22,

    A_10A: 18,
    A_10C: 20,

    # special
    IL_76MD: 13,
    An_26B: 13,
    An_30M: 13,
    Yak_40: 13,
    S_3B_Tanker: 13,

    A_50: 8,
    E_3A: 8,
    C_130: 8,

    # armor
    Armor.MBT_T_55: 4,
    Armor.MBT_T_80U: 8,
    Armor.MBT_T_90: 10,

    Armor.MBT_M60A3_Patton: 6,
    Armor.MBT_M1A2_Abrams: 9,

    Armor.ATGM_M1134_Stryker: 6,
    Armor.APC_BTR_80: 6,

    AirDefence.AAA_Vulcan_M163: 5,
    AirDefence.SAM_Avenger_M1097: 10,
    AirDefence.SAM_Patriot_ICC: 15,

    AirDefence.AAA_ZU_23_on_Ural_375: 5,
    AirDefence.SAM_SA_18_Igla_MANPADS: 8,
    AirDefence.SAM_SA_19_Tunguska_2S6: 10,
    AirDefence.SAM_SA_8_Osa_9A33: 15,

    # ship
    CV_1143_5_Admiral_Kuznetsov: 100,
    CVN_74_John_C__Stennis: 100,
}

UNIT_BY_TASK = {
    FighterSweep: [
        C_101CC,
        AJS37,
        F_5E,
        MiG_23MLD,
        MiG_25PD,
        MiG_31,
        Su_27,
        Su_33,
        MiG_15bis,
        MiG_21Bis,
        MiG_29A,
        FA_18C_hornet,
        AV8BNA,
        F_15C,
        M_2000C,
    ],
    CAS: [
        A_10A,
        A_10C,
        Su_25T,
        Su_24M,
        Su_17M4,
        L_39ZA,
        MiG_29G,
        Su_34,
    ],

    Transport: [
        IL_76MD,
        An_26B,
        An_30M,
        Yak_40,

        S_3B_Tanker,
        C_130,
    ],
    AWACS: [E_3A, A_50, ],

    CAP: [Armor.MBT_T_90, Armor.MBT_T_80U, Armor.MBT_T_55, Armor.MBT_M1A2_Abrams, Armor.MBT_M60A3_Patton, Armor.ATGM_M1134_Stryker, Armor.APC_BTR_80, ],
    AirDefence: [
        AirDefence.AAA_Vulcan_M163,
        AirDefence.SAM_Avenger_M1097,
        AirDefence.SAM_Patriot_ICC,

        AirDefence.AAA_ZU_23_on_Ural_375,
        AirDefence.SAM_SA_18_Igla_MANPADS,
        AirDefence.SAM_SA_19_Tunguska_2S6,
        AirDefence.SAM_SA_8_Osa_9A33,
    ],
    Carriage: [CVN_74_John_C__Stennis, CV_1143_5_Admiral_Kuznetsov, ],
}

UNIT_BY_COUNTRY = {
    "Russia": [
        C_101CC,
        AJS37,
        F_5E,
        MiG_23MLD,
        MiG_25PD,
        MiG_31,
        Su_27,
        Su_33,
        MiG_15bis,
        MiG_21Bis,
        MiG_29A,
        M_2000C,

        A_10A,
        A_10C,
        Su_25T,
        Su_24M,
        Su_17M4,
        L_39ZA,
        MiG_29G,
        Su_34,

        IL_76MD,
        An_26B,
        An_30M,
        Yak_40,
        A_50,

        AirDefence.AAA_ZU_23_on_Ural_375,
        AirDefence.SAM_SA_18_Igla_MANPADS,
        AirDefence.SAM_SA_19_Tunguska_2S6,
        AirDefence.SAM_SA_8_Osa_9A33,

        Armor.APC_BTR_80,
        Armor.MBT_T_90,
        Armor.MBT_T_80U,
        Armor.MBT_T_55,
        CV_1143_5_Admiral_Kuznetsov],

    "USA": [
        F_15C,
        FA_18C_hornet,
        AV8BNA,
        AJS37,
        F_5E,
        M_2000C,
        MiG_21Bis,
        MiG_15bis,

        A_10A,
        A_10C,

        S_3B_Tanker,
        C_130,
        E_3A,

        Armor.MBT_M1A2_Abrams,
        Armor.MBT_M60A3_Patton,
        Armor.ATGM_M1134_Stryker,

        AirDefence.AAA_Vulcan_M163,
        AirDefence.SAM_Avenger_M1097,
        AirDefence.SAM_Patriot_ICC,

        CVN_74_John_C__Stennis,
    ],
}

PLANE_PAYLOAD_OVERRIDES = {
    FA_18C_hornet: {
        "*": "AIM-9M*6, AIM-7M*2, FUEL*3",
    },

    MiG_21Bis: {
        "*": "Patrol, medium range",
    }
}

PLANE_LIVERY_OVERRIDES = {
    FA_18C_hornet: "VFA-34",
}

UnitsDict = typing.Dict[UnitType, int]
PlaneDict = typing.Dict[FlyingType, int]
ArmorDict = typing.Dict[VehicleType, int]
AirDefenseDict = typing.Dict[AirDefence, int]
StartingPosition = typing.Optional[typing.Union[ShipGroup, Airport, Point]]


def unit_task(unit: UnitType) -> Task:
    for task, units in UNIT_BY_TASK.items():
        if unit in units:
            return task

    assert False


def find_unittype(for_task: Task, country_name: str) -> typing.List[UnitType]:
    return [x for x in UNIT_BY_TASK[for_task] if x in UNIT_BY_COUNTRY[country_name]]


def unit_type_name(unit_type) -> str:
    return unit_type.id and unit_type.id or unit_type.name


def task_name(task) -> str:
    if task == AirDefence:
        return "AirDefence"
    else:
        return task.name


def choose_units(for_task: Task, factor: float, count: int, country: str) -> typing.Collection[UnitType]:
    suitable_unittypes = find_unittype(for_task, country)
    suitable_unittypes.sort(key=lambda x: PRICES[x])

    idx = int(len(suitable_unittypes) * factor)
    variety = int(count + count * factor / 2)

    index_start = min(idx, len(suitable_unittypes) - variety)
    index_end = min(idx + variety, len(suitable_unittypes))
    return suitable_unittypes[index_start:index_end]


def _validate_db():
    # check unit by task uniquity
    total_set = set()
    for t, unit_collection in UNIT_BY_TASK.items():
        for unit_type in unit_collection:
            assert unit_type not in total_set, "{} is duplicate".format(unit_type)
            total_set.add(unit_type)

    # check country allegiance
    for unit_type in total_set:
        did_find = False
        for country_units_list in UNIT_BY_COUNTRY.values():
            if unit_type in country_units_list:
                did_find = True
        assert did_find, "{} not in country list".format(unit_type)

    # check prices
    for unit_type in total_set:
        assert unit_type in PRICES, "{} not in prices".format(unit_type)

_validate_db()