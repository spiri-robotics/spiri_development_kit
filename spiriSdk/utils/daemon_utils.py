import docker, docker.errors, time

from nicegui import run
from loguru import logger

from spiriSdk.utils.SDKRobot import SDKRobot
from spiriSdk.settings import SDK_ROOT

DATA_DIR = SDK_ROOT / 'data'
ROBOTS_DIR = SDK_ROOT / 'robots'
ROOT_DIR = SDK_ROOT

robots : dict[str, SDKRobot]= {}
active_sys_ids = []

async def init_robots():
    global robots
    from spiriSdk.utils.card_utils import displayCards
    logger.info(f"Initializing Docker robots for robots...")

    for robot_dir in DATA_DIR.iterdir():
        robot_name = robot_dir.name

        if robot_dir.exists():
            logger.debug(f"Starting a daemon for: {robot_name}")
            new_robot = SDKRobot(robot_name, folder=ROBOTS_DIR / robot_name / 'services')
            robots[robot_name] = new_robot
            displayCards.refresh()

            robot_sys = str(robot_name).rsplit('_', 1)
            active_sys_ids.append(int(robot_sys[1]))
            
    logger.debug(f"Starting services for {len(robots)} robots...")
    for robot in robots.values():
        await run.io_bound(robot.start())
        
    logger.success("Docker robots initialized.")


async def start_container(robot_name):
    logger.info(f'Starting container for {robot_name}...')
    await run.io_bound(robots[robot_name].start())


async def stop_container(robot_name):
    if robot_name not in robots:
        return f"No daemon found for {robot_name}.", 'negative'

    await robots[robot_name].stop()
        
    logger.success(f'Container {robot_name} stopped')
    return f"Container {robot_name} stopped", 'positive'


async def restart_container(robot_name: str):
    if robots[robot_name].container.status == 'running':
        await run.io_bound(lambda: stop_container(robot_name))
    await start_container(robot_name)
    logger.success(f"Container {robot_name} restarted successfully.")