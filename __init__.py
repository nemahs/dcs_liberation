#!/usr/bin/env python3
import logging
import os
import re
import sys
sys.path.insert(1, "./submodules/dcs") # Add pydcs submodule to python load path
import dcs
import logging

import ui.corruptedsavemenu
import ui.mainmenu
import ui.newgamemenu
import ui.window
from game.game import Game
from userdata import persistency, logging as logging_module

#TODO: Change args to argparse

assert len(sys.argv) >= 3, "__init__.py should be started with two mandatory arguments: %UserProfile% location and application version"

persistency.setup(sys.argv[1])
dcs.planes.FlyingType.payload_dirs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources\\payloads")]

VERSION_STRING = sys.argv[2]
logging_module.setup_version_string(VERSION_STRING)
logging.info("Using {} as userdata folder".format(persistency.base_path()))



window = ui.window.Window()

def proceed_to_main_menu(game: Game):
    """ Moves game to main menu

        @param game  Game to move to main menu
    """
    menu = ui.mainmenu.MainMenu(window, None, game)
    menu.display()


def is_version_compatible(save_version: str):
    """ Check that the save version is compatible with the current version

        @param save_version  String version to check fo compatibility
        @return True if save_version is compatible with current version, False otherwise.
    """
    current_version_components = re.split(r"[\._]", VERSION_STRING)
    save_version_components = re.split(r"[\._]", save_version)

    if "--ignore-save" in sys.argv:
        return False

    if current_version_components == save_version_components:
        return True

    if save_version in ["1.4_rc1", "1.4_rc2", "1.4_rc3", "1.4_rc4", "1.4_rc5", "1.4_rc6"]:
        return False

    if current_version_components[:2] == save_version_components[:2]:
        return True

    return False


window = ui.window.Window()

try:
    game = persistency.restore_game()
    if not game or not is_version_compatible(game.settings.version):
        ui.newgamemenu.NewGameMenu(window, window.start_new_game).display()
    else:
        game.settings.version = VERSION_STRING
        proceed_to_main_menu(game)
except Exception as e:
    logging.exception(e)
    ui.corruptedsavemenu.CorruptedSaveMenu(window).display()

window.run()
