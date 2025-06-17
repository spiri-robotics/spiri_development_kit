from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import addRobot, displayCards
from spiriSdk.pages.tools import tools

@ui.page('/')
async def home():
    await styles()
    await header()

    with ui.row().classes('justify-items-stretch w-full'):
        ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
        ui.space()
        await tools()

    displayCards()