from nicegui import ui
import os
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import yaml
import re
from pathlib import Path
from spiriSdk.utils.new_robot_utils import ensure_options_yaml, ROBOTS_DIR, save_robot_config, display_robot_options

robots = ensure_options_yaml()

@ui.page('/new_robots')
async def new_robots():
    await styles()

    selected_robot = {'name': None}
    selected_additions = ["gimbal"]
    selected_options = {}

    def on_select(robot_name: str):
        selected_robot['name'] = robot_name
        display_robot_options(robot_name, selected_additions, selected_options, options_container)
    
    ui.label('New Robot').classes('text-h5')
    ui.select([f'{robot}' for robot in robots], label='Select robot type', on_change=lambda e: on_select(e.value)).classes('w-full')

    options_container = ui.column()

    ui.button('Add Robot', color='secondary', on_click=lambda: save_robot_config(selected_robot['name'], selected_options)).classes('q-mt-md')
    ui.button('back to manage page', color='secondary', on_click=lambda: ui.navigate.to('/manage_robots'))
