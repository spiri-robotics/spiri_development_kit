import asyncio

from nicegui import ui
from pathlib import Path

from spiriSdk.pages.sidebar import sidebar
from spiriSdk.pages.tools import tools
from spiriSdk.ui.styles import styles
from spiriSdk.utils.card_utils import addRobot, displayCards

ENV_FILE_PATH = Path('.env')

def read_env():
    env = {}
    if ENV_FILE_PATH.exists():
        for line in ENV_FILE_PATH.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip().strip('"')
    return env

@ui.page('/')
async def home():
    await styles()
    sidebar()

    with ui.row(align_items='center').classes('w-full'):
        ui.markdown('## Dashboard').classes('pb-2')
        ui.space()
        ui.button('Add Robot', on_click=addRobot, color='secondary')
        await tools()
    
    ui.separator()

    await asyncio.sleep(0.5)
    await displayCards()