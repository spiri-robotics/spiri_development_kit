from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.pages.edit_robot import edit_robot


@ui.page('/manage_robots')
async def manage_robots():
    await styles()
    await header()

    with ui.dialog() as addRobot, ui.card(align_items='stretch'):
        await new_robots()

        with ui.card_actions().props('align=center'):
            ui.button('Add', on_click=addRobot.close)  #color='#FAC528'
            ui.button('Cancel', on_click=addRobot.close)

    ui.button('Add Robot', on_click=addRobot.open)

    with ui.card(align_items='stretch'):
        with ui.card_actions().props('align=between'):
            ui.label('[robot name]')
            ui.label('[status]')
        with ui.card_section().props('horizontal'):
            ui.button('Start').classes('m-2')  #color='#9EDFEC'
            ui.button('Restart').classes('m-2')
            ui.button('Stop').classes('m-2')

            with ui.dialog() as editRobot, ui.card():
                await edit_robot()

                with ui.card_actions().props('align=center'):
                    ui.button('Save', on_click=editRobot.close)  #color='#FAC528'
                    ui.button('Cancel', on_click=editRobot.close)
            ui.button('Edit Robot', on_click=editRobot.open).classes('m-2')  #color='#9EDFEC'
            ui.button('Delete Robot', on_click=lambda: ui.navigate.to('/delete_robot')).classes('m-2')
