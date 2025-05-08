from nicegui import ui, binding, app, run
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
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

worlds = {

}

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
        launch_app(cmd)
    except FileNotFoundError:
        print(f"File not found: {name}. Make sure it is installed and available in the PATH.")

@ui.page('/tools')
async def tools():
    with ui.dialog() as gz_dialog, ui.card():
        with ui.card().props('').classes('rounded-lg'):
            ui.label('World Start Time State').props('class="text-lg text-center"')
            world_auto_run = ui.toggle(['Running', 'Paused'], value='Paused')
        with ui.card().props('').classes('rounded-lg'):
            with ui.dropdown_button('worlds', auto_close=True, color='#20788a').classes('text-lg text-center'):
                await find_worlds()
                for dir, name in worlds.items():
                    ui.item(name, on_click=lambda dir=dir, name=name: run_world(dir, name, world_auto_run.value))
    await styles()
    await header()
    with ui.grid(columns=3):
        for app_name, command in applications.items():
            with ui.button(on_click=lambda cmd=command: launch_app(cmd), color='warning').classes('rounded-1/2'):   # old color for all 3: color='#20788a'
                ui.label(app_name).classes('text-lg text-center')
        with ui.button(on_click=gz_dialog.open, color='#20788a').classes('rounded-1/2'):
            ui.label('Launch Gazebo').classes('text-lg text-center')
            
        