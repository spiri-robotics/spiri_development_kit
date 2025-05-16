from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer

@ui.page('/')
async def home():
    await styles()
    await header()
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    container = RobotContainer(destination)

    await container.displayButtons()
    await container.displayCards()