import docker, docker.errors, yaml
from spiriSdk.docker.dindocker import DockerInDocker
from nicegui import run
from docker.errors import NotFound, APIError
from spiriSdk.settings import SIM_ADDRESS, SDK_ROOT, GROUND_CONTROL_ADDRESS
from pathlib import Path
from loguru import logger
import asyncio

DATA_DIR = SDK_ROOT / 'data'
ROBOTS_DIR = SDK_ROOT / 'robots'
ROOT_DIR = SDK_ROOT

daemons = {}
active_sys_ids = []

async def init_daemons():
    global daemons
    from spiriSdk.utils.card_utils import displayCards
    logger.info(f"Initializing Docker daemons for robots...")

    for robot_dir in DATA_DIR.iterdir():
        robot_name = robot_dir.name

        if robot_dir.exists():
            logger.debug(f"Starting a daemon for: {robot_name}")
            dind = DockerInDocker("docker:dind", robot_name)
            daemons[robot_name] = dind

            await run.io_bound(dind.ensure_started)
            displayCards.refresh()

            robot_sys = str(robot_name).rsplit('_', 1)
            active_sys_ids.append(int(robot_sys[1]))
            
    logger.debug(f"Starting services for {len(daemons)} robots...")
    for robot_name in list(daemons.keys()):
        message = await start_services(robot_name)
        logger.info(message)
        
    logger.success("Docker daemons initialized.")
        

async def start_services(robot_name: str):
    if robot_name not in daemons:
        return f"No daemon found for {robot_name}."

    container = daemons[robot_name].container
    if container is None:
        return f"No container found for {robot_name}. It may not be started yet."

    try:
        container.reload()
    except NotFound:
        daemons[robot_name].container = None
        return f"Container {robot_name} is already removed."

    if container.status != "running":
        return f"Container {robot_name} is not running."

    try:
        robot_type = "_".join(robot_name.split('_')[:-1])
        # services_dir = os.path.join(ROBOTS_DIR, robot_type, "services")
        services_dir = ROBOTS_DIR / robot_type / 'services'
        logger.debug(f"Checking services in {services_dir} for {robot_name}...")
        if not services_dir.exists():
            return f"Services directory {services_dir} does not exist for {robot_name}."

        for service_path in services_dir.iterdir():
            # service_path = os.path.join(services_dir, service)
            if not service_path.iterdir():
                logger.debug(f"Skipping {service_path} as it is not a directory.")
                continue

            compose_path = service_path / 'docker-compose.yaml'
            if not compose_path.exists():
                compose_path = service_path / "docker-compose.yml"
                if not compose_path.exists():
                    logger.error(f"docker-compose file not found for {robot_name}/{service_path.name} at {compose_path}. Skipping.")
                    continue

            # Step 3: Load compose YAML
            try:
                with open(compose_path, 'r') as f:
                    compose_data = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error reading {compose_path}: {e}")
                continue

            # Step 4: Check x-spiri-sdk-autostart
            if compose_data.get("x-spiri-sdk-autostart", True):
                logger.info(f"Autostarting: {robot_name}/{service_path.name}")
                # Step 5: Run `docker compose up -d` inside the DinD container
                inside_path = f"/robots/{robot_type}/services/{service_path.name}"
                command = f"docker compose --env-file=/data/config.env -f {inside_path}/{compose_path.name} up -d"
                result = await run.io_bound(lambda r=robot_name, c=command, i=inside_path: daemons[r].container.exec_run(c, workdir=i))
                print(result.output.decode())

    except Exception as e:
        return f"Error starting services for {robot_name}: {str(e)}"
    
    return f"Services for {robot_name} started successfully."

def display_daemon_status(robot_name):
    try:
        container = daemons[robot_name].container
        if container is None:
            return 'not created or removed'
        container.reload()
        status = container.status
        if status == 'running':
            socket_path = f'unix:///tmp/dind-sockets/spirisdk_{robot_name}.socket'
            try:
                client = docker.DockerClient(base_url=socket_path)
                states = {
                    "Running": len(client.containers.list(filters={'status': 'running'})),
                    "Restarting": len(client.containers.list(filters={'status': 'restarting'})),
                    "Exited": len(client.containers.list(filters={'status': 'exited'})),
                    "Created": len(client.containers.list(filters={'status': 'created'})),
                    "Paused": len(client.containers.list(filters={'status': 'paused'})),
                    "Dead": len(client.containers.list(filters={'status': 'dead'})),
                }
                if all(count == 0 for count in states.values()):
                    return 'Starting up'
                else:
                    return states
            except Exception as e:
                return 'Starting up'
        else:
            return status
    except docker.errors.NotFound:
        return 'stopped'
    except Exception as e:
        return f'error: {str(e)}'
    
async def check_stopped(robot_name):
    status = display_daemon_status(robot_name)
    if isinstance(status, dict):
        return
    while status not in  ('stopped', 'removing'):
        logger.debug(f"Waiting for {robot_name} to stop... Current status: {status}")
        await asyncio.sleep(1)

async def start_container(robot_name):
    logger.info(f'Starting container for {robot_name}...')
    await run.io_bound(daemons[robot_name].ensure_started)

def stop_container(robot_name):
    if robot_name not in daemons:
        return f"No daemon found for {robot_name}.", 'negative'

    container = daemons[robot_name].container
    if container is None:
        return f"No container found for {robot_name}. It may have already been removed.", 'negative'

    try:
        container.reload()
    except NotFound:
        daemons[robot_name].container = None
        return f"Container {robot_name} is already removed.", 'info'

    if container.status != "running":
        return f"Container {robot_name} is not running or has already stopped.", 'info'

    try:
        container.stop()
        return f"Container {robot_name} stopped.", 'positive'
    except NotFound:
        daemons[robot_name].container = None
        return f"Container {robot_name} was already removed before stopping.", 'info'
    except APIError as e:
        if e.response is not None and e.response.status_code == 404:
            daemons[robot_name].container = None
            return f"Container {robot_name} was already removed before stopping.", 'negative'
        else:
            raise e

async def restart_container(robot_name: str):
    status = display_daemon_status(robot_name)
    if status == 'running' or isinstance(status, dict):
        message = await run.io_bound(lambda: stop_container(robot_name))
        logger.info(message)
    await check_stopped(robot_name)
    await start_container(robot_name)
    logger.info(f"Container {robot_name} restarted successfully.")