from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import DaemonEvent

container = None
loaded = False

@ui.page('/')
async def home():
    global loaded
    await styles()
    await header()
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    global container
    container = RobotContainer(destination)
    
    await DaemonEvent.notify()