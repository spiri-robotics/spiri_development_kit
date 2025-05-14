import os
from spiriSdk.dindocker import DockerInDocker
from nicegui import run, ui
import docker

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

def start_container(robot_name: str):
    daemons[robot_name].ensure_started()
    ui.notify(f"Container {robot_name} started.")

def stop_container(robot_name: str):
    daemons[robot_name].container.stop()
    ui.notify(f"Container {robot_name} stopped.")

def restart_container(robot_name: str):
    stop_container(robot_name)
    start_container(robot_name)
    ui.notify(f"Container {robot_name} restarted.")

async def display_daemon_status(robot_name):
    try:
        container = daemons[robot_name].container
        container.reload()
        return container.status
    except docker.errors.NotFound:
        return 'stopped'
    except Exception as e:
        return f'error: {str(e)}'