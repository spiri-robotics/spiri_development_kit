from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.utils.gazebo_models import Robot
from spiriSdk.utils.gazebo_worlds import World
from spiriSdk.utils.gazebo_worlds import find_worlds
import subprocess

#Commands to run applications
applications = {
    'rqt': ['rqt'],
    'rvis2': ['rviz2']
}

#Arrays to hold temporary information for page such as robots and worlds
robots = []
worlds = {}
running_worlds = [['empty_world','empty_world.world']]
selected_dir = {'empty_world': 'empty_world.world'}

def launch_app(command): 
    """Run command to start applications with the exception of gazebo"""
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")

async def prep_bot(robot_name: str ='mu', robot_type: str ='spiri-mu') -> None: 
    """Create a new robot and send it to launch function to be added to the world"""
    world_spawn = None
    if world_spawn is None:

        #Tells the robot which world to add it to. Will eventually be changed to a list of running worlds
        world_spawn = running_worlds[0][0] 
    robot_number = len(robots) + 1

    mu = Robot(robot_name, robot_type, robot_number)
    
    robots.append(mu)
    
    await mu.launch_robot(world_spawn)
    print(f"Robot {mu.name}{mu.number} added to the world '{world_spawn}'")
    return None

def select_world(dir) -> World: 
    """Might look dumb but allows the ui selection element to return a world object"""
    return World(dir, worlds[dir])

@ui.page('/tools')
async def tools():

    #Sets worlds to the dict of gazebo worlds found in the worlds directory
    worlds = await find_worlds() 
    
    with ui.dialog() as gz_dialog, ui.card().classes('items-center'):
    
        #with ui.card().props('').classes('rounded-lg'):
            ui.label('World Start Time State').classes('text-h5')

            ui.space()

            #variable to tell the world time whether to initially run or not
            world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused').props('size=md toggle-color="[#274c77]"')
    
        #with ui.card().props('').classes('rounded-lg'):
            w = ui.select(list(worlds.keys()), value='empty_world').classes('text-lg')
            
            async def start_and_close(): 
                """function to combine starting the world and closing the dialog"""
                selected = w.value
                selected_world = worlds[selected]
                print(f"Selected world: {selected_world.get_name()}")
                running_worlds.clear()

                # Set running_worlds to the world that was selected as well as start running the gazebo simulation
                running_worlds.append(await selected_world.run_world(world_auto_run.value)) 
                
                gz_dialog.close()
            
            ui.space()

            ui.button('Start World', 
                      on_click=start_and_close,
                      color='secondary'
                      ).classes('text-base')
            ui.space()
    
    await styles()

    with ui.row():
        for app_name, command in applications.items():
            ui.button(f'{app_name}', on_click=lambda cmd=command: launch_app(cmd), color='secondary').classes('text-base')  # old color for all 3: color='#20788a'
        ui.button('Launch Gazebo', on_click=gz_dialog.open, color='secondary').classes('text-base')
            
        