from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.utils.new_robot_utils import ensure_options_yaml, display_robot_options

robots = ensure_options_yaml()
selected_options = {}
selected_robot = None
selected_additions = []

options_container = None

def on_select(robot_name: str):
    global selected_robot
    selected_robot = robot_name
    selected_additions.clear()
    selected_options.clear()
    options_container.clear()
    selected_additions.append(robot_name)
    display_robot_options(robot_name, selected_additions, selected_options, options_container)
    return selected_robot

def display_fields():
    ui.label('New Robot').classes('text-h5')
    with ui.row().classes('w-full'):
        ui.select([f'{robot}' for robot in robots], label='Select robot type', on_change=lambda e: on_select(e.value)).classes('w-full')

    global options_container
    options_container = ui.column().classes('w-full')

@ui.page('/new_robots')
async def new_robots():

    await styles()
    display_fields()