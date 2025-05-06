from nicegui import ui, binding, app, run
from spiriSdk.pages.header import header
import time
import docker
import subprocess
import asyncio

applications = {
    'rqt': ['rqt'],
    'rvis2': ['rviz2'],
    'Gazebo': ['gazebo']
}

def launch_app(command):
    try:
        subprocess.Popen(command)
    except FileNotFoundError:
        print(f"Command not found: {command}. Make sure it is installed and available in the PATH.")


@ui.page('/tools')
async def tools():
    await header()
    with ui.grid(columns=3):
        for app_name, command in applications.items():
            with ui.card().props('flat').classes('justify-center items-center'):
                ui.label(app_name).tailwind.font_weight('extrabold')
                ui.button('Launch', on_click=lambda cmd=command: launch_app(cmd), color='#a0dbea').props('ripple icon-right="img:/icons/arrow_circle_right.png"').tailwind.font_weight('extrabold')