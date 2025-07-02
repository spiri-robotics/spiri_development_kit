from nicegui import ui
from pathlib import Path
from spiriSdk.ui.styles import styles
from spiriSdk.utils.gazebo_utils import World, WORLD_PATHS, gz_world
import subprocess
import os

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
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")


@ui.page('/tools')
async def tools():
    WORLD_NAMES = list(WORLD_PATHS.keys())
    global gz_world
    with ui.dialog() as gz_dialog, ui.card().classes('items-center'):
    
        ui.label('World Start Time State').classes('text-h5')
        ui.space()

        #variable to tell the world time whether to initially run or not
        world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused').classes('text-base justify-center').props('size=md toggle-color="[#274c77]"')

        w = ui.select(WORLD_NAMES, value='empty_world').classes('text-base w-full')
        ui.space()
        
        async def start_and_close(): 
            """function to combine starting the world and closing the dialog"""
            if (world_auto_run.value == 'Running'):
                world_run_value = '-r '
            else:
                world_run_value = ''
            await gz_world.reset(w.value, world_run_value)
            
            gz_dialog.close()
        
        ui.button('Start World', 
                    on_click=start_and_close,
                    color='secondary'
                    ).classes('text-base')

    await styles()

    with ui.row():
        for app_name, command in applications.items():
            ui.button(f'{app_name}', on_click=lambda cmd=command: launch_app(cmd), color='secondary')  # old color for all 3: color='#20788a'
        ui.button('Launch Gazebo', on_click=gz_dialog.open, color='secondary')
        