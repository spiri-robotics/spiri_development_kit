from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.utils.new_robot_utils import ensure_options_yaml, display_robot_options
from spiriSdk.utils.InputChecker import InputChecker

robots = ensure_options_yaml()
selected_options = {}
selected_robot = None
# selected_additions = []

options_container = None

def on_select(e: ui.select, checker: InputChecker):
    checker.checkSelect(e)
    checker.reset()
    robot_name = str(e.value)
    global selected_robot
    selected_robot = robot_name
    # selected_additions.clear()
    selected_options.clear()
    options_container.clear()
    # selected_additions.append(robot_name)
    display_robot_options(robot_name, selected_options, options_container, checker)
    return selected_robot

def display_fields(checker: InputChecker):
    with ui.label('New Robot').classes('text-h5'):
        ui.label('Fields marked with a * are required').classes('text-base text-gray-500 dark:text-gray-300')
    with ui.row().classes('w-full'):
        i = ui.select([f'{robot}' for robot in robots], label='Select robot type*', on_change=lambda e: on_select(e.sender, checker)).classes('w-full')
        checker.add(i, False)

    global options_container
    options_container = ui.column().classes('w-full')

@ui.page('/new_robots')
async def new_robots(checker):

    await styles()
    display_fields(checker)