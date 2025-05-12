from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.pages.new_robots import new_robots
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
        await new_robots()

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=addRobot.close)
            ui.button('Add', color='secondary', on_click=lambda: container.displayCards(addRobot))

    container.displayAddButton(addRobot)

    #container.display(addRobot, bigCard)