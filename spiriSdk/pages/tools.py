from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.gazebo_models import Robot
from spiriSdk.utils.gazebo_worlds import World
from spiriSdk.utils.gazebo_worlds import find_worlds
import subprocess

applications = {
    'rqt': ['rqt'],
    'rvis2': ['rviz2']
}

robots = []
worlds = {}
running_worlds = [['','']]
selected_dir = {'empty_world': 'empty_world.world'}

def launch_app(command): 
    """Run command to start applications with the exception of gazebo"""
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")

async def prep_bot(world_spawn: str =None) -> None: 
    """Create a new robot and add it to the world"""
    if world_spawn is None:
        #Tells the robot which world to add it to. Will eventually be changed to a list of running worlds
        world_spawn = running_worlds[0][0] 
    robot_number = len(robots) + 1

    mu = Robot('spiri_mu_', robot_number)
    
    robots.append(mu)
    
    await mu.launch_robot(world_spawn)
    print(f"Robot {mu.name}{mu.number} added to the world '{world_spawn}'")
    return None

def select_world(dir) -> World: 
    """Might look dumb but allows the ui selection element to return a world object"""
    return World(dir, worlds[dir])

@ui.page('/tools')
async def tools():
    
    worlds = await find_worlds() #Sets worlds to the dict of gazebo worlds found in the worlds directory
    
    with ui.dialog() as gz_dialog, ui.card():
    
        with ui.card().props('').classes('rounded-lg'):
            ui.label('World Start Time State').props('class="text-lg text-center"')

            #variable to tell the world time whether to initially run or not
            world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused') 
    
        with ui.card().props('').classes('rounded-lg'):
            w = ui.select(list(worlds.keys()))
            
            async def start_and_close(): 
                """function to combine starting the world and closing the dialog"""
                selected = w.value
                selected_world = worlds[selected]
                print(f"Selected world: {selected_world.get_name()}")
                running_worlds.clear()

                # Set running_worlds to the world that was selected as well as start running the gazebo simulation
                running_worlds.append(await selected_world.run_world(world_auto_run.value)) 
                
                gz_dialog.close()
            
            ui.button('Start World', 
                      on_click=start_and_close,
                      color='warning'
                      ).classes('rounded-1/2')
    
    await styles()
    await header()

    with ui.grid(columns=3):
        for app_name, command in applications.items():
            with ui.button(on_click=lambda cmd=command: launch_app(cmd), color='warning').classes('rounded-1/2'):   # old color for all 3: color='#20788a'
                ui.label(app_name).classes('text-lg text-center')
        with ui.button(on_click=gz_dialog.open, color='warning').classes('rounded-1/2'):
            ui.label('Launch Gazebo').classes('text-lg text-center')
        ui.button("add mu", on_click=lambda: prep_bot(), color='warning').classes('text-lg rounded-1/2')
            
        