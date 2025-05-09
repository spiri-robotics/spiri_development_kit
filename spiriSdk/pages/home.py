from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header

@ui.page('/')
async def home():
    await styles()

    ui.button('tools', on_click=lambda: ui.navigate.to('/tools'), color='secondary')
    ui.button('manage', on_click=lambda: ui.navigate.to('/manage_robots'), color='secondary')

    with ui.row().classes('w-full'):
        with ui.card().classes('w-[calc(50vw-24px)]'):
            ui.label('Welcome to the Spiri SDK!').classes('text-lg')
        with ui.card().classes('w-[calc(50vw-24px)]'):
            ui.label('Welcome to the Spiri SDK!').classes('text-lg')