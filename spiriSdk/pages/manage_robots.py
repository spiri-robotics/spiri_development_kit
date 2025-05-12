from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.pages import new_robots #, selected_options, selected_robot
from spiriSdk.utils.new_robot_utils import save_robot_config, init_daemons
from spiriSdk.pages.edit_robot import edit_robot
from spiriSdk.utils.card_utils import RobotContainer

@ui.page('/manage_robots')
async def manage_robots():
    await styles()
    await header()
    
    destination = ui.card().classes('w-full p-0 shadow-none')
    container = RobotContainer(destination)

    with ui.dialog() as editRobot, ui.card():
        await edit_robot()

        with ui.card_actions().props('align=stretch'):
            ui.button('Save', on_click=editRobot.close)
            ui.button('Cancel', on_click=editRobot.close)
            
    with ui.dialog() as addRobot, ui.card(align_items='stretch').classes('w-full'):
        await new_robots.new_robots()

        async def add_robot():
            addRobot.close()
            await save_robot_config(new_robots.selected_robot, new_robots.selected_options)
            container.displayCards(addRobot, editRobot)

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=addRobot.close)
            ui.button('Add (elena)', color='secondary', on_click=lambda: container.displayCards(addRobot, editRobot))
            ui.button('Add (alice)', color='secondary', on_click=add_robot)

    container.displayAddButton(addRobot)

    #container.display(addRobot, bigCard)