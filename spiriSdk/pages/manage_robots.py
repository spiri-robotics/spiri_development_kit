from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.pages.edit_robot import edit_robot


@ui.page('/manage_robots')
async def manage_robots():
    await styles()
    await header()

    with ui.dialog() as addRobot, ui.card(align_items='stretch').classes('w-full'):
        await new_robots()

        with ui.card_actions().props('align=center'):
            ui.button('Add', color='secondary', on_click=addRobot.close)
            ui.button('Cancel', color='secondary', on_click=addRobot.close)

    ui.button('Add Robot', on_click=addRobot.open, color='secondary')
    ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')

    with ui.card().classes('w-full'):
        with ui.row(align_items='stretch').classes('w-full'):
            with ui.card_section():
                ui.label('[robot name]').classes('mb-5')
                ui.label('[status]').classes('mt-5')
            ui.space()
            with ui.card_actions():
                ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                ui.button('Stop', icon='stop', color='warning').classes('m-1')
                ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                with ui.dialog() as editRobot, ui.card():
                    await edit_robot()

                    with ui.card_actions().props('align=stretch'):
                        ui.button('Save', on_click=editRobot.close)
                        ui.button('Cancel', on_click=editRobot.close)

                with ui.dropdown_button(icon='settings', color='secondary'):
                    ui.item('Edit', on_click=editRobot.open)
                    ui.item('Delete')
