from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import DaemonEvent

@ui.page('/')
async def home():
    await styles()
    await header()
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    container = RobotContainer(destination)
    
    empty = container.is_empty()
    print(empty) # debug
    if empty:
        await DaemonEvent.notify()