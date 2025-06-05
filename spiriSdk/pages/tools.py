from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.utils.gazebo_utils import Gazebo
import subprocess
gz = Gazebo()

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

    #Sets worlds to the dict of gazebo worlds found in the worlds directory
    global gz
    
    with ui.dialog() as gz_dialog, ui.card().classes('items-center'):
    
        ui.label('World Start Time State').classes('text-h5')
        ui.space()

        #variable to tell the world time whether to initially run or not
        world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused').classes('text-base justify-center').props('size=md toggle-color="[#274c77]"')

        w = ui.select(list(gz.worlds.keys()), value='empty_world').classes('text-base w-full')
        ui.space()
        
        async def start_and_close(): 
            """function to combine starting the world and closing the dialog"""

            # Set running_worlds to the world that was selected as well as start running the gazebo simulation
            await gz.start_world(w.value, world_auto_run.value)
            
            gz_dialog.close()
        
        ui.button('Start World', 
                    on_click=start_and_close,
                    color='secondary'
                    ).classes('text-base')
    
    async def print_running_worlds(gz=gz):
        await gz.get_running_worlds()
        print("Running worlds:", gz.running_worlds)
        ui.notify(f"Running worlds: {gz.running_worlds}")

    await styles()

    with ui.row():
        for app_name, command in applications.items():
            ui.button(f'{app_name}', on_click=lambda cmd=command: launch_app(cmd), color='secondary').classes('text-base')  # old color for all 3: color='#20788a'
        ui.button('Launch Gazebo', on_click=gz_dialog.open, color='secondary').classes('text-base')
        ui.button('Show Running Worlds', on_click=print_running_worlds, color='info').classes('text-base')
        