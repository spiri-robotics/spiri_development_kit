from nicegui import ui
from spiriSdk.ui.styles import styles
from spiriSdk.pages.header import header
from spiriSdk.utils.card_utils import RobotContainer
from spiriSdk.utils.daemon_utils import DaemonEvent
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

container = None

container = None

@ui.page('/')
async def home():
    await styles()
    await header()

    env_data = read_env()
    registries = env_data.get("REGISTRIES", "").split(",") if env_data.get("REGISTRIES") else []
    registries = [r.strip() for r in registries if r.strip()]
    auth_registries = env_data.get("AUTH_REGISTRIES", "").split(",") if env_data.get("AUTH_REGISTRIES") else []

    required_host = "git.spirirobotics.com"
    required_auth = f"{required_host}:Aurora:bc1423e2fea3aa3e997028142b9844276be9ec28"

    if required_host not in registries or required_auth not in auth_registries:
        with ui.card().classes('w-full p-4 bg-red-100 dark:bg-red-800 text-red-900 dark:text-red-100'):
            ui.label("Warning: Required Spiri authentication entry is missing, please check the settings page.").classes('text-lg')
            
    destination = ui.card().classes('w-full p-0 shadow-none dark:bg-[#212428]')
    global container
    container = RobotContainer(destination)
    await DaemonEvent.notify()