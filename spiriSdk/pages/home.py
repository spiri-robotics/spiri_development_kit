from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.sidebar import sidebar
from spiriSdk.utils.card_utils import addRobot, displayCards
from spiriSdk.pages.tools import tools
from pathlib import Path
import asyncio

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

    env_data = read_env()
    registries = env_data.get("REGISTRIES", "").split(",") if env_data.get("REGISTRIES") else []
    registries = [r.strip() for r in registries if r.strip()]
    auth_registries = env_data.get("AUTH_REGISTRIES", "").split(",") if env_data.get("AUTH_REGISTRIES") else []

    required_host = "git.spirirobotics.com"
    has_required_auth = any(entry.strip().startswith(f"{required_host}:") for entry in auth_registries)

    if required_host not in registries or not has_required_auth:
        with ui.card().classes('w-full p-4 bg-red-100 dark:bg-red-800 text-red-900 dark:text-red-100'):
            ui.label("Warning: Required Spiri authentication entry is missing, please check the settings page.").classes('text-lg')
        
    with ui.row(align_items='center').classes('w-full'):
        ui.markdown('## Dashboard').classes('pb-2')
        ui.space()
        ui.button('Add Robot', on_click=addRobot, color='secondary')
        await tools()
    
    ui.separator()

    await asyncio.sleep(0.5)
    displayCards()