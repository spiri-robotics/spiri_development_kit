from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import DaemonEvent
from spiriSdk.utils.daemon_utils import daemons
from nicegui import context

container = None
loaded = False

@ui.page('/')
async def home():
    global loaded
    await styles()
    await header()
    print(daemons)
    
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    global container
    container = RobotContainer(destination)

    await container.displayButtons()
        
    await DaemonEvent.notify()