import os
from spiriSdk.dindocker import DockerInDocker  
from nicegui import run

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')

daemons = {}

async def init_daemons() -> dict:
    global daemons
    
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
    for daemon in daemons.values():
        await run.io_bound(daemon.cleanup)
    daemons.clear()