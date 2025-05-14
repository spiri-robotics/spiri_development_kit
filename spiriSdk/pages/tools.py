from nicegui import ui, binding, app, run
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.gazebo_models import Robot
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

def launch_app(command):
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")

async def find_worlds(p = Path('./worlds')):
    try:
        for subdir in p.iterdir():
            world_in_dir = []
            if subdir.is_dir():
                for world in subdir.rglob('*.world'):
                    worlds.update({subdir.name:world.name})
        print(worlds)
    except FileNotFoundError:
        print(f"Directory not found: {p}. Make sure it exists.")
        return []

async def run_world(dir, name, auto_run):
    try:
        if auto_run == 'Running':
            cmd = ['gz', 'sim', '-r', f'./worlds/{dir}/worlds/{name}']
        else:
            cmd = ['gz', 'sim', f'./worlds/{dir}/worlds/{name}']
        running_worlds.clear()
        running_worlds.append([dir, name])

        launch_app(cmd)
        return None
        
    except FileNotFoundError:
        print(f"File not found: {name}. Make sure it is installed and available in the PATH.")

async def prep_bot(world=None):
    if world is None:
        world = running_worlds[0][0]
    robot_number = len(robots) + 1 
    mu = Robot('spiri_mu', robot_number)
    robots.append(mu)
    await mu.launch_robot(world)
    print(f"Robot {mu.name}{mu.number} added to the world '{world}'")
    return None

@ui.page('/tools')
async def tools():
    with ui.dialog() as gz_dialog, ui.card():
        with ui.card().props('').classes('rounded-lg'):
            ui.label('World Start Time State').props('class="text-lg text-center"')
            world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused')
        with ui.card().props('').classes('rounded-lg'):
            with ui.dropdown_button('worlds', auto_close=True).classes('text-lg text-center'):
                await find_worlds()
                for dir, name in worlds.items():
                    ui.item(name, on_click=lambda dir=dir, name=name: run_world(dir, name, world_auto_run.value))
    await styles()
    
    with ui.row():
        for app_name, command in applications.items():
            ui.button(f'{app_name}', on_click=lambda cmd=command: launch_app(cmd), color='secondary').classes('text-base')  # old color for all 3: color='#20788a'
        ui.button('Launch Gazebo', on_click=gz_dialog.open, color='secondary').classes('text-base')
        ui.button('Add Mu', on_click=lambda: prep_bot(), color='secondary').classes('text-base')
            
        