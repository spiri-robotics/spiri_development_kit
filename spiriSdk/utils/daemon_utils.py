import os
from spiriSdk.dindocker import DockerInDocker
from nicegui import run, ui

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')

daemons = {}

async def init_daemons() -> dict:
    global daemons
    print("Initializing Daemons...")
    
    daemons = {}

    for robot_name in os.listdir(DATA_DIR):
        if os.path.isdir(os.path.join(DATA_DIR, robot_name)):
            daemons[robot_name] = DockerInDocker("docker:dind", robot_name)

    for daemon in daemons.values():
        await run.io_bound(daemon.ensure_started)

    return daemons

async def on_startup():
    global daemons
    daemons = await init_daemons()

async def on_shutdown():
    daemons = await init_daemons()
    for daemon in daemons.values():
        await run.io_bound(daemon.cleanup)
    daemons.clear()

async def start_container(robot_name: str):
    await daemons[robot_name].ensure_started()
    ui.notify(f"Container {robot_name} started.")

async def stop_container(robot_name: str):
    await daemons[robot_name].stop()
    ui.notify(f"Container {robot_name} stopped.")

async def restart_container(robot_name: str):
    await stop_container(robot_name)
    await start_container(robot_name)
    ui.notify(f"Container {robot_name} restarted.")

async def display_daemon_status(robot_name: str):
    print(f"Fetching status for {robot_name}")
    daemons = await init_daemons()
    print(f"Daemon initialized: {daemons.get(robot_name)}")
    return daemons[robot_name].get_status()