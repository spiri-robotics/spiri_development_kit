from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.pages.tools import tools
from spiriSdk.pages.new_robots import new_robots, selected_options, selected_robot, clear_fields
from spiriSdk.utils.new_robot_utils import save_robot_config
from spiriSdk.pages.edit_robot import edit_robot
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import init_daemons

@ui.page('/')
async def home():
    await styles()
    await header()
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    container = RobotContainer(destination, None, None)

    with ui.dialog() as editRobot, ui.card():
        await edit_robot()

        with ui.card_actions().props('align=stretch'):
            ui.button('Save', on_click=editRobot.close)
            ui.button('Cancel', on_click=editRobot.close)

    with ui.dialog() as addRobot, ui.card(align_items='stretch').classes('w-full'):
        await new_robots()

        async def add_robot(button):
            button = button.props(add='loading')
            await save_robot_config(selected_robot, selected_options)

            # Close dialog and reset fields + button 
            addRobot.close()
            button.delete()
            button = ui.button('Add', color='secondary', on_click=lambda e: add_robot(e.sender))
            await clear_fields()

            await container.displayCards()   
            ui.notify(f"Robot {selected_robot} added successfully!")

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=addRobot.close).classes('text-base')
            ui.button('Add', color='secondary', on_click=lambda e: add_robot(e.sender)).classes('text-base')

    container.assignAddRobot(addRobot)
    container.assignEditRobot(editRobot)

    await container.displayButtons()

    await container.displayCards()