from nicegui import ui
from spiriSdk.pages.header import header
from pathlib import Path
from spiriSdk.ui.styles import styles
ENV_FILE_PATH = Path('.env')

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
    ui.label("Settings").classes('text-6xl')
    ui.separator()
    
    global auth_registries, registries
    auth_registries = []
    registries = []
    await header()
    await styles()
    env_data = read_env()

    ui.label("Authentication Settings").classes('text-4xl')
    ui.label("Edit the list of sites that require authentication here")
    ui.separator()

    registries = env_data.get("REGISTRIES", "").split(",") if env_data.get("REGISTRIES") else []
    registries = [r.strip() for r in registries if r.strip()]

    def update_env():
        env_data["REGISTRIES"] = ",".join(registries)
        env_data["AUTH_REGISTRIES"] = ",".join([
            ":".join(entry) for entry in auth_registries
        ])
        write_env(env_data)
        ui.notify("✅ Environment file updated")

    ### --- AUTH_REGISTRIES SECTION ---
    ui.label("Authenticated Registries (AUTH_REGISTRIES)").classes('text-xl mt-6')

    with ui.card().classes('w-full p-4 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'):
        with ui.row().classes('items-center mb-2'):
            ui.icon('info', size='24px').classes('text-blue-500')
            ui.label("How to authenticate with the Spiri Gitea repository:").classes('font-bold text-lg')
        ui.markdown(
            """
    - **hostname:** `git.spirirobotics.com`
    - **username:** *Your Gitea username*
    - **token:**  
    1. Go to your Gitea profile picture → **Settings** → **Applications**
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

    auth_table = ui.column()

    def refresh_auth_ui():
        auth_table.clear()
        for host, user, token in auth_registries:
            with auth_table:
                with ui.row():
                    ui.label(f'{host}').classes("min-w-[150px]")
                    ui.label(f'{user}').classes("min-w-[100px]")
                    ui.label(f'{token[:6]}...').classes("min-w-[200px]")  # Mask token
                    ui.button("", icon='delete', on_click=lambda h=host, u=user: delete_auth(h, u), color='secondary')

    def delete_auth(host, user):
        global auth_registries
        global registries
        auth_registries = [entry for entry in auth_registries if not (entry[0] == host and entry[1] == user)]
        registries = [r for r in registries if r != host]
        update_env()
        refresh_auth_ui()

    def add_auth():
        host = host_input.value.strip()
        user = user_input.value.strip()
        token = token_input.value.strip()
        if host and user and token and [host, user, token] not in auth_registries:
            auth_registries.append([host, user, token])
            registries.append(host)
            update_env()
            refresh_auth_ui()
            host_input.value = ""
            user_input.value = ""
            token_input.value = ""

    refresh_auth_ui()
    with ui.row().classes("mt-2"):
        host_input = ui.input(label="Host")
        user_input = ui.input(label="Username")
        token_input = ui.input(label="Token", password=True)
        ui.button("Add Auth Registry", on_click=add_auth,color='secondary')