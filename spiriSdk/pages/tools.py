from functools import partial
from nicegui import ui, binding, app, run
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.gazebo_models import Robot
from spiriSdk.utils.gazebo_worlds import World
from spiriSdk.utils.gazebo_worlds import find_worlds
import time
import docker
import subprocess
import asyncio
import spiriSdk.icons as icons
from pathlib import Path

applications = {
    'rqt': ['rqt'],
    'rvis2': ['rviz2']
}

robots = []

worlds = {}

running_worlds = [['','']]

selected_dir = {'empty_world': 'empty_world.world'}

def launch_app(command):
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")

async def prep_bot(world=None):
    if world is None:
        world = running_worlds[0][0]
    robot_number = len(robots) + 1 
    mu = Robot('spiri_mu', robot_number)
    robots.append(mu)
    await mu.launch_robot(world)
    print(f"Robot {mu.name}{mu.number} added to the world '{world}'")
    return None

def select_world(dir):
    return World(dir, worlds[dir])

@ui.page('/tools')
async def tools():
    worlds = await find_worlds()
    with ui.dialog() as gz_dialog, ui.card():
        with ui.card().props('').classes('rounded-lg'):
            ui.label('World Start Time State').props('class="text-lg text-center"')
            world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused')
        with ui.card().props('').classes('rounded-lg'):
            w = ui.select(
                list(worlds.keys())
            )
            async def start_and_close():
                selected = w.value
                print(selected)
                selected_world = World(worlds[selected], selected)
                running_worlds.clear()
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
            
        