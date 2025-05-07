from nicegui import ui
from pages.header import header
from pages.new_robots import new_robots

@ui.page('/manage_robots')
async def manage_robots():
    await header()

    with ui.dialog() as dialog, ui.card():
        await new_robots()
        ui.button('Close', on_click=dialog.close)

    ui.button('Add Robot', on_click=dialog.open, color='#FAC528')

    with ui.card(align_items='stretch'):
        with ui.card_actions().props('align=between'):
            ui.label('[robot name]')
            ui.label('[status]')
        with ui.card_section().props('horizontal'):
            ui.button('Edit Robot', on_click=lambda: ui.navigate.to('/edit_robot'), color='#9EDFEC').classes('m-2')
            ui.button('Delete Robot', on_click=lambda: ui.navigate.to('/delete_robot'), color='#9EDFEC').classes('m-2')
            ui.button('View Robots', on_click=lambda: ui.navigate.to('/view_robots'), color='#9EDFEC').classes('m-2')
