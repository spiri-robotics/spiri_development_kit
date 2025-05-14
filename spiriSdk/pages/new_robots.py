from nicegui import ui
import os
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import yaml
import re
from pathlib import Path
from spiriSdk.utils.new_robot_utils import ensure_options_yaml, ROBOTS_DIR, save_robot_config, display_robot_options

robots = ensure_options_yaml()
selected_options = {}
selected_robot = None
selected_additions = []

@ui.page('/new_robots')
async def new_robots():
    await styles()

    def on_select(robot_name: str):
        selected_robot = robot_name
        selected_additions.clear()
        selected_options.clear()
        options_container.clear()
        selected_additions.append(robot_name)
        display_robot_options(robot_name, selected_additions, selected_options, options_container)
        return selected_robot
    
    ui.label('New Robot').classes('text-h5')
    with ui.row().classes('w-full'):
        ui.input('Robot Name', placeholder='Enter robot name').classes('w-[400px]')
        ui.select([f'{robot}' for robot in robots], label='Select robot type', on_change=lambda e: on_select(e.value)).classes('w-[400px]')

    options_container = ui.column()

    #Old add button: ui.button('Add Robot', color='secondary', on_click=lambda: save_robot_config(selected_robot, selected_options)).classes('q-mt-md')
    
    ui.button('back to manage page', color='secondary', on_click=lambda: ui.navigate.to('/'))
