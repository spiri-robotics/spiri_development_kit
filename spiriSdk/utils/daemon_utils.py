from loguru import logger
from dotenv import dotenv_values

from spiriSdk.classes.DinDockerRobot import DinDockerRobot
from spiriSdk.classes.LocalRobot import LocalRobot
from spiriSdk.classes.RemoteRobot import RemoteRobot
from spiriSdk.settings import SDK_ROOT
# Define paths for data and robots directories
DATA_DIR = SDK_ROOT / 'data'
ROBOTS_DIR = SDK_ROOT / 'robots'
ROOT_DIR = SDK_ROOT
# Initialize global variables
robots : dict[str, DinDockerRobot]= {}
active_sys_ids = []

async def init_robots():
    """Initialize Docker robots listed in the data directory."""
    global robots
    from spiriSdk.utils.card_utils import displayCards
    logger.info(f"Initializing Docker robots for robots...")

    for robot_dir in DATA_DIR.iterdir():
        robot_name = robot_dir.name
        robot_type = "_".join(robot_name.split('_')[:-1])
        env_path = DATA_DIR / robot_name / 'config.env'
        
        if not env_path.exists():
            logger.warning(f"No config.env found in {robot_dir}, skipping.")
            continue

        try:
            config = dotenv_values(env_path)
        except Exception as e:
            logger.error(f"Failed to read {env_path}: {e}")
            continue
        
        robot_class = config.get("ROBOT_CLASS", "Docker in Docker").strip()

        if robot_dir.exists():
            logger.debug(f"Starting a daemon for: {robot_name}")
            
            if robot_class == 'Docker in Docker':
                new_robot = DinDockerRobot(robot_name)
            elif robot_class == 'Local':
                new_robot = LocalRobot(robot_name, ROBOTS_DIR / robot_type / 'services')
            else: 
                new_robot = RemoteRobot(robot_name, ROBOTS_DIR / robot_type / 'services')
            robots[robot_name] = new_robot
            displayCards.refresh()

            robot_sys = str(robot_name).rsplit('_', 1)
            active_sys_ids.append(int(robot_sys[1]))
            
    logger.debug(f"Starting services for {len(robots)} robots...")
    for robot in robots.values():
        await robot.start()
        
    logger.success("Docker robots initialized.")