from nicegui import ui, binding, app, run
from spiriSdk.pages.header import header
import time
import docker
import subprocess
import asyncio
import spiriSdk.icons as icons
from pathlib import Path

applications = {
    'rqt': ['rqt'],
    'rvis2': ['rviz2'],
    'Gazebo': ['gazebo']
}

worlds = {

}

def launch_app(command):
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")

def find_worlds(p = Path('../worlds')):
    try:
        for subdir in p.iterdir():
            world_in_dir = []
            if subdir.is_dir():
                for world in subdir.rglob('*.world'):
                    if world.name not in world_in_dir:
                        world_in_dir.append(world.name)
                worlds.update({subdir.name:world_in_dir})
        print(worlds)
    except FileNotFoundError:
        print(f"Directory not found: {p}. Make sure it exists.")
        return []


@ui.page('/tools')
async def tools():
    await header()
    with ui.grid(columns=3):
        for app_name, command in applications.items():
            with ui.button(on_click=lambda cmd=command: launch_app(cmd), color='#a0dbea').classes('rounded-1/2 '):
                ui.label(app_name).classes('text-lg text-center')
    with ui.dropdown_button('GZ', auto_close=True):
        find_worlds()
        for dir in worlds:
            for world in worlds[dir]:
                ui.item(world, on_click=lambda: ui.notify('Launching ' + world))