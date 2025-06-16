from nicegui import ui, Client
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer, addRobot
from spiriSdk.utils.daemon_utils import DaemonEvent
from spiriSdk.pages.tools import tools

container = None

@ui.page('/')
async def home(client: Client):
    await styles()
    await header()

    with ui.row().classes('justify-items-stretch w-full'):
        ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
        # ui.button(on_click=lambda: ui.navigate.to('/new_robots'), color='secondary').classes('text-base')
        ui.space()
        await tools()
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    global container
    container = RobotContainer(destination, client)
    await DaemonEvent.notify()