import os
from spiriSdk.dindocker import DockerInDocker
from nicegui import run, ui
import docker
from docker.errors import NotFound, APIError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')

daemons = {}

async def init_daemons() -> dict:
    global daemons
    print("Initializing Daemons...")
    for robot_name in os.listdir(DATA_DIR):
        if os.path.isdir(os.path.join(DATA_DIR, robot_name)):
            daemons[robot_name] = DockerInDocker("docker:dind", robot_name)

    for daemon in daemons.values():
        await run.io_bound(daemon.ensure_started)

async def on_startup():
    await init_daemons()

async def on_shutdown():
    for daemon in daemons.values():
        await run.io_bound(daemon.cleanup)
    daemons.clear()

async def start_container(robot_name: str):
    print(f"Starting container for {robot_name}...")
    await run.io_bound(daemons[robot_name].ensure_started)
    ui.notify(f"Container {robot_name} started.")

def stop_container(robot_name: str):
    if robot_name not in daemons:
        ui.notify(f"No daemon found for {robot_name}.")
        return

    container = daemons[robot_name].container

    if container is None:
        ui.notify(f"No container found for {robot_name}. It may have already been removed.")
        return

    try:
        container.reload()  # Refresh container state
    except NotFound:
        daemons[robot_name].container = None
        ui.notify(f"Container {robot_name} is already removed.")
        return

    if container.status != "running":
        ui.notify(f"Container {robot_name} is not running or has already stopped.")
        return

    try:
        container.stop()
        ui.notify(f"Container {robot_name} stopped.")
    except NotFound:
        daemons[robot_name].container = None
        ui.notify(f"Container {robot_name} was already removed before stopping.")
    except APIError as e:
        if e.response is not None and e.response.status_code == 404:
            daemons[robot_name].container = None
            ui.notify(f"Container {robot_name} was already removed before stopping.")
        else:
            raise

async def restart_container(robot_name: str):
    await run.io_bound(lambda: stop_container(robot_name))  # wrap sync function
    await start_container(robot_name)
    ui.notify(f"Container {robot_name} restarted.")

async def display_daemon_status(robot_name):
    try:
        container = daemons[robot_name].container
        if container is None:
            return 'not created or removed'
        container.reload()
        return container.status
    except docker.errors.NotFound:
        return 'stopped'
    except Exception as e:
        return f'error: {str(e)}'