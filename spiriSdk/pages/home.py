from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import DaemonEvent

container = None

@ui.page('/')
async def home():
    print('home initialized')
    await styles()
    await header()
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    global container
    container = RobotContainer(destination)

    await container.displayButtons()
    
    if container.is_empty():
        await DaemonEvent.notify()