from nicegui import ui
from pathlib import Path
from spiriSdk.ui.styles import styles
from spiriSdk.utils.gazebo_utils import World, WORLD_PATHS, gz_world
from spiriSdk.utils.InputChecker import InputChecker
import subprocess
from loguru import logger

#Commands to run applications
applications = {
    'rqt': ['rqt'],
    'rviz2': ['rviz2']
}

def launch_app(command): 
    """Run command to start applications with the exception of gazebo"""
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        logger.warning(f"Command not found: {command}. Make sure it is installed and available in the PATH.")


@ui.page('/tools')
async def tools():
    WORLD_NAMES = list(WORLD_PATHS.keys())
    global gz_world
    with ui.dialog() as gz_dialog, ui.card().classes('items-center'):
    
        select_check = InputChecker()
        ui.label('Gazebo Launch Settings').classes('text-h5')
        w = ui.select(WORLD_NAMES, label='Select World*').classes('text-base w-full')
        select_check.add(w, False)
        w.on_value_change(lambda e, ch=select_check: ch.checkSelect(e.sender))
        ui.space()
        
        async def start_and_close(): 
            if(w.value != None):
                await gz_world.reset(w.value)
                gz_dialog.close()
            else:
                ui.notify("Please Select a World")
        
        ui.button(
            'Start World', 
            on_click=start_and_close,
            color='secondary'
        ).bind_enabled_from(select_check, 'isValid')
        print(select_check.isValid)

    with ui.row():
        ui.button('Launch Gazebo', on_click=gz_dialog.open, color='secondary')
        for app_name, command in applications.items():
            ui.button(f'{app_name}', on_click=lambda cmd=command: launch_app(cmd), color='secondary')  # old color for all 3: color='#20788a'
        