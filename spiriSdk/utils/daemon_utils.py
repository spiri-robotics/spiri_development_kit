import os
from spiriSdk.docker.dindocker import DockerInDocker
from nicegui import run, ui
import docker
from docker.errors import NotFound, APIError
import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
ROBOTS_DIR = os.path.join(ROOT_DIR, 'robots')

daemons = {}

async def init_daemons() -> dict:
    global daemons
    print("Initializing Daemons...")
    for robot_name in os.listdir(DATA_DIR):
        robot_path = os.path.join(DATA_DIR, robot_name)
        if os.path.isdir(robot_path):
            dind = DockerInDocker("docker:dind", robot_name)
            daemons[robot_name] = dind
            await run.io_bound(dind.ensure_started)

            robot_type = "-".join(robot_name.split('-')[:-1])
            services_dir = os.path.join(ROBOTS_DIR, robot_type, "services")
            print(f"Checking services in {services_dir} for {robot_name}...")
            if not os.path.exists(services_dir):
                print(f"Services directory {services_dir} does not exist for {robot_name}. Skipping.")
                continue

            for service in os.listdir(services_dir):
                service_path = os.path.join(services_dir, service)
                if not os.path.isdir(service_path):
                    print(f"Skipping {service_path} as it is not a directory.")
                    continue

                compose_path = os.path.join(service_path, "docker-compose.yaml")
                if not os.path.exists(compose_path):
                    print(f"docker-compose.yaml not found for {robot_name}/{service} at {compose_path}. Skipping.")
                    continue

                # Step 3: Load compose YAML
                try:
                    with open(compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)
                except Exception as e:
                    print(f"Error reading {compose_path}: {e}")
                    continue

                # Step 4: Check x-spiri-sdk-autostart
                if compose_data.get("x-spiri-sdk-autostart", True):
                    print(f"Autostarting: {robot_name}/{service}")
                    # Step 5: Run `docker compose up -d` inside the DinD container
                    inside_path = f"/robots/{robot_type}/services/{service}"
                    command = f"docker compose --env-file=/data/config.env -f {inside_path}/docker-compose.yaml up -d"
                    result = await run.io_bound(lambda: daemons[robot_name].container.exec_run(command, workdir=inside_path))
                    print(result.output.decode())

async def on_shutdown():
    for daemon in daemons.values():
        await run.io_bound(daemon.cleanup)
    daemons.clear()

async def start_container(robot_name: str):
    print(f"Starting container for {robot_name}...")
    await run.io_bound(daemons[robot_name].ensure_started)
    ui.notify(f"Container {robot_name} started.")

def stop_container(robot_name: str) -> str:
    if robot_name not in daemons:
        return f"No daemon found for {robot_name}."

    container = daemons[robot_name].container
    if container is None:
        return f"No container found for {robot_name}. It may have already been removed."

    try:
        container.reload()
    except NotFound:
        daemons[robot_name].container = None
        return f"Container {robot_name} is already removed."

    if container.status != "running":
        return f"Container {robot_name} is not running or has already stopped."

    try:
        container.stop()
        return f"Container {robot_name} stopped."
    except NotFound:
        daemons[robot_name].container = None
        return f"Container {robot_name} was already removed before stopping."
    except APIError as e:
        if e.response is not None and e.response.status_code == 404:
            daemons[robot_name].container = None
            return f"Container {robot_name} was already removed before stopping."
        else:
            raise

async def restart_container(robot_name: str):
    message = await run.io_bound(lambda: stop_container(robot_name))
    ui.notify(message)
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