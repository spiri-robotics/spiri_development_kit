from nicegui import ui
from spiriSdk.ui.styles import styles

@ui.page('/')
async def home():
    await styles()

    with ui.row():
        ui.button('tools', on_click=lambda: ui.navigate.to('/tools'), color='secondary')
        ui.button('manage', on_click=lambda: ui.navigate.to('/manage_robots'), color='secondary')

    with ui.row().classes('w-full'):
        with ui.card().classes('w-[calc(50vw-24px)]'):
            ui.label('Welcome to the Spiri SDK!').classes('text-lg')