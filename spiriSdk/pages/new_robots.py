from nicegui import ui

from spiriSdk.ui.styles import styles
from spiriSdk.utils.InputChecker import InputChecker
from spiriSdk.utils.new_robot_utils import display_robot_options

robots = ['Spiri Mu']
selected_options = {}
selected_robot = None

options_container = None

def on_select(e: ui.select, checker: InputChecker):
    checker.checkSelect(e)
    checker.reset()
    robot_type = str(e.value)
    if robot_type == 'Spiri Mu':
        robot_type = 'spiri_mu'
    global selected_robot
    selected_robot = robot_type
    selected_options.clear()
    options_container.clear()
    display_robot_options(robot_type, selected_options, options_container, checker)
    return selected_robot

def display_fields(checker: InputChecker):
    with ui.label('New Robot').classes('text-h5'):
        ui.label('Fields marked with a * are required').classes('text-base italic text-gray-700 dark:text-gray-300')
    with ui.row().classes('w-full'):
        i = ui.select([f'{robot}' for robot in robots], label='Select robot type*', on_change=lambda e: on_select(e.sender, checker)).classes('w-full')
        checker.add(i, False)

    global options_container
    options_container = ui.column().classes('w-full')

@ui.page('/new_robots')
async def new_robots(checker):

    await styles()
    display_fields(checker)