from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import os



@ui.page('/edit_robot')

async def edit_robot(robotID):
    ui.label(f'this is the edit robot page. editing {robotID}')

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    folder_name = f"{robotID}"
    folder_path = os.path.join(ROOT_DIR, "data", folder_name)
    config_path = os.path.join(folder_path, "config.env")

    currentSettings = {}
    currentSettings.clear()

    with open(config_path, 'r') as options:
        for line in options:
            s = line.split('=')
            currentSettings[s[0]] = s[1]

    for key, val in currentSettings.items():
        ui.label(key)