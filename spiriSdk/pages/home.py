from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import addRobot, displayCards
from spiriSdk.pages.tools import tools
from pathlib import Path

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
    await header()

    env_data = read_env()
    registries = env_data.get("REGISTRIES", "").split(",") if env_data.get("REGISTRIES") else []
    registries = [r.strip() for r in registries if r.strip()]
    auth_registries = env_data.get("AUTH_REGISTRIES", "").split(",") if env_data.get("AUTH_REGISTRIES") else []

    required_host = "git.spirirobotics.com"
    has_required_auth = any(entry.strip().startswith(f"{required_host}:") for entry in auth_registries)

    if required_host not in registries or not has_required_auth:
        with ui.card().classes('w-full p-4 bg-red-100 dark:bg-red-800 text-red-900 dark:text-red-100'):
            ui.label("Warning: Required Spiri authentication entry is missing, please check the settings page.").classes('text-lg')
        
    with ui.row().classes('justify-items-stretch w-full'):
        ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
        ui.space()
        await tools()

    displayCards()