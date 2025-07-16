import docker, docker.errors, time

from nicegui import run
from loguru import logger

from spiriSdk.utils import SDKRobot
from spiriSdk.settings import SDK_ROOT

DATA_DIR = SDK_ROOT / 'data'
ROBOTS_DIR = SDK_ROOT / 'robots'
ROOT_DIR = SDK_ROOT

robots = {}
active_sys_ids = []

async def init_robots():
    global robots
    from spiriSdk.utils.card_utils import displayCards
    logger.info(f"Initializing Docker robots for robots...")

    for robot_dir in DATA_DIR.iterdir():
        robot_name = robot_dir.name

        if robot_dir.exists():
            logger.debug(f"Starting a daemon for: {robot_name}")
            new_robot = SDKRobot(robot_name, folder=robot_dir)
            robots[robot_name] = new_robot

            await run.io_bound(new_robot.start())
            displayCards.refresh()

            robot_sys = str(robot_name).rsplit('_', 1)
            active_sys_ids.append(int(robot_sys[1]))
            
    logger.debug(f"Starting services for {len(robots)} robots...")
    for robot in robots.values():
        message = await robot.start_services()
        logger.info(message)
        
    logger.success("Docker robots initialized.")


async def start_container(robot_name):
    logger.info(f'Starting container for {robot_name}...')
    await run.io_bound(robots[robot_name].start())


def stop_container(robot_name):
    if robot_name not in robots:
        return f"No daemon found for {robot_name}.", 'negative'

    container = robots[robot_name].container
    try:
        container.stop()
    except Exception as e:
        logger.error(f"Error stopping container {robot_name}: {e}")
        return f"Error stopping container {robot_name}: {str(e)}", 'negative'

    while True:
        try:
            container.reload()  # Refresh container status
            status = container.status
            if status == "exited" or status == "stopped":
                break
        except docker.errors.NotFound:
            # Container has been removed, consider it stopped
            break
        except Exception as e:
            logger.error(f"Error checking container status for {robot_name}: {e}")
            return(f'Error checking container status for {robot_name}: {e}'), 'negative'

        time.sleep(1)
        logger.debug(f"Waiting for container {robot_name} to stop... {status}")
        
    logger.success(f'Container {robot_name} stopped')
    return f"Container {robot_name} stopped", 'positive'


async def restart_container(robot_name: str):
    if robots[robot_name].container.status == 'running':
        await run.io_bound(lambda: stop_container(robot_name))
    await start_container(robot_name)
    logger.success(f"Container {robot_name} restarted successfully.")