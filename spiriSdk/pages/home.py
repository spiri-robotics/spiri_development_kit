from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.gazebo_utils import Gazebo
from spiriSdk.utils.daemon_utils import DaemonEvent

@ui.page('/')
async def home():
    await styles()
    await header()
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    container = RobotContainer(destination)
    
    if container.is_empty():
        await DaemonEvent.notify()