from nicegui import ui
from spiriSdk.pages.sidebar import sidebar
from pathlib import Path
from spiriSdk.ui.styles import styles
import os
ENV_FILE_PATH = Path(os.environ.get("SDK_ROOT", "."))/'.env'

auth_registries = []
registries = []

def read_env():
    """Parse .env file into a dictionary, stripping quotation marks."""
    env = {}
    if ENV_FILE_PATH.exists():
        for line in ENV_FILE_PATH.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip().strip('"')
    else:
        ui.notify("No env file found")
    return env

def write_env(env_dict):
    """Write dictionary back to .env, adding double quotes around values."""
    lines = [f'{k}="{v}"' for k, v in env_dict.items()]
    ENV_FILE_PATH.write_text('\n'.join(lines))

@ui.page('/settings')
async def settings():
    await styles()
    sidebar()
    
    ui.markdown("## Settings")
    ui.separator()
    
    global auth_registries, registries
    auth_registries = []
    registries = []
    env_data = read_env()

    ui.label("Authentication Settings").classes('text-2xl font-')
    ui.label("Edit the list of sites that require authentication here").classes('font-light text-base')
    
    registries = env_data.get("REGISTRIES", "").split(",") if env_data.get("REGISTRIES") else []
    registries = [r.strip() for r in registries if r.strip()]

    def update_env():
        env_data["REGISTRIES"] = ",".join(registries)
        env_data["AUTH_REGISTRIES"] = ",".join([
            ":".join(entry) for entry in auth_registries
        ])
        write_env(env_data)
        ui.notify("Environment file updated", type='positive')
        
    def add_auth():
        host = host_input.value.strip()
        user = user_input.value.strip()
        token = token_input.value.strip()
        if host and user and token and [host, user, token] not in auth_registries:
            auth_registries.append([host, user, token])
            registries.append(host)
            update_env()
            display_registries.refresh()
            host_input.value = ""
            user_input.value = ""
            token_input.value = ""

    ### --- AUTH_REGISTRIES SECTION ---
    with ui.row(align_items='stretch').classes('w-full pb-4'):
        with ui.card(align_items='stretch').classes("p-4 w-[30%] max-w-[600px]"):
            host_input = ui.input(label="Host", value='git.spirirobotics.com')
            user_input = ui.input(label="Username")
            token_input = ui.input(label="Token", password=True, password_toggle_button=True)
            ui.button("Add Registry", on_click=add_auth, color='secondary')
        
        with ui.card().classes('p-4 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 w-[50%] max-w-[700px]'):
            with ui.row().classes('items-center mb-2'):
                ui.icon('info', size='24px').classes('text-blue-500')
                ui.label("How to authenticate with the Spiri Gitea repository:").classes('font-bold text-lg')
            ui.markdown(
                """
        - **hostname:** `git.spirirobotics.com`
        - **username:** *Your Gitea username*
        - **token:**  
            1. In Gitea, go to [**Settings** → **Applications**](https://git.spirirobotics.com/user/settings/applications)
            2. Name a token and give it **read** permissions for both packages and repos
            3. Click **Generate Token** and copy the resulting token printed at the top of the page
            4. You have acquired your Gitea access token!
                """
            ).classes('text-base')

    auth_registries_raw = env_data.get("AUTH_REGISTRIES", "")
    for entry in auth_registries_raw.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 3:
            auth_registries.append(parts)

    @ui.refreshable
    def display_registries():
        with ui.column().classes('w-full'):
            if len(auth_registries) == 0:
                ui.label('No registries authenticated.').classes('text-base font-light')
            for host, user, token in auth_registries:
                with ui.row().classes('w-full'):
                    ui.label(f'{host}').classes("w-[200px] text-base font-light")
                    ui.label(f'{user}').classes("w-[150px] text-base font-light")
                    ui.label(f'{token[:6]}*******************').classes("w-[250px] text-base font-light")  # Mask token
                    ui.button("", icon='delete', on_click=lambda h=host, u=user: delete_auth(h, u), color='negative')

    def delete_auth(host, user):
        global auth_registries
        global registries
        auth_registries = [entry for entry in auth_registries if not (entry[0] == host and entry[1] == user)]
        registries = [r for r in registries if r != host]
        update_env()
        display_registries.refresh()
        
    ui.label('Authenticated Registries:').classes('text-xl font-normal')
    display_registries()