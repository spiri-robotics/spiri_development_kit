from loguru import logger
from pathlib import Path
from nicegui import run
import docker
import shutil
import yaml
import time

from spiriSdk.classes.DockerRobot import DockerRobot
from spiriSdk.docker.dindocker import DockerInDocker
from spiriSdk.utils.daemon_utils import robots
from spiriSdk.settings import SDK_ROOT, ROBOTS_DIR
class DinDockerRobot(DockerRobot):
    """
    An example implementation of the robot class.
    This robot has its own Docker in Docker instance to run its services.
    """
    
    def __init__(self, name: str):
        """
        Initialize a DinDockerRobot instance.
        
        param name: The name of the robot, of the format <robot_type>_<sys_id>.
        param robot_type: The type of the robot, which is derived from the name (e.x. spiri_mu).
        param services_folder: The services_folder where the robot's services are located.
            This folder should contain a docker-compose.yml file to start the robot's services.
        param env_path: The path to the environment file for the robot.
        param connection_url: The URL to connect to the Docker daemon.
        param spawned: A boolean indicating whether the robot has been spawned into a simulation environment.
        param running: A boolean indicating whether the robot's services are currently running.
        param dind: An instance of DockerInDocker to manage the Docker in Docker environment.
        param docker_client: The Docker client used to interact with the Docker daemon.
        param container: The Docker container instance for the robot.
        """
        self.name = name
        self.robot_type = "-".join(self.name.split('-')[:-1])
        self.services_folder : Path = ROBOTS_DIR / self.robot_type / 'services'
        self.env_path : Path = SDK_ROOT / 'data' / self.name / 'config.env'
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        self.dind = DockerInDocker(name=self.name, services_folder=self.services_folder)
        self.docker_client : docker.DockerClient | None = None
        self.container : docker.models.containers.Container | None = None
        
    async def start(self) -> None:
        """Starts the robot by starting the dind instance and the services."""
        await self.dind.ensure_started()
        self.docker_client = self.dind.get_docker_client()
        self.container = self.dind.get_container()
        await self.start_services()
        self.running = True
        
    async def stop(self) -> None:
        """Stops the robot by stopping the dind instance."""
        try:
            self.container.stop()
        except Exception as e:
            logger.error(f"Error stopping container {self.name}: {e}")
            return f"Error stopping container {self.name}: {str(e)}", 'negative'

        while True:
            try:
                self.container.reload()  # Refresh container status
                status = self.container.status
                if status == "exited" or status == "stopped":
                    break
            except docker.errors.NotFound:
                # Container has been removed, consider it stopped
                break
            except Exception as e:
                logger.error(f"Error checking container status for {self.name}: {e}")

            time.sleep(1)
            logger.debug(f"Waiting for container {self.name} to stop... {status}")
            
        logger.success(f'Container {self.name} stopped')

        self.docker_client = None
        self.container = None
        self.running = False

    async def delete(self) -> None:
        """
        Cleans up resources associated with the robot.
        This includes stopping the robot's services, removing it from the system,
        closing the Docker client, and unspawning the robot if it was spawned 
        into a simulation environment.
        """
        self.dind.cleanup()
        await self.stop_services()
        await self.remove_from_system()
        if self.docker_client is not None:
            try:
                self.docker_client.close()
            except Exception as e:
                logger.error(f"Error closing Docker client: {str(e)}")
        if self.spawned:
            await self.unspawn()
        self.spawned = False
        self.running = False
        
    def get_ip(self) -> str:
        """
        This method returns the IP at which the robot can be accessed.
        
        Returns:
            str: The IP address of the robot.
        """
        return self.dind.get_ip()
    
    async def start_services(self):
        try:
            logger.debug(f"Checking services in {self.services_folder.name} for {self.name}...")
            if not self.services_folder.is_dir():
                return f"Services directory {self.services_folder} does not exist for {self.name}."

            for service_path in self.services_folder.iterdir():
                if not service_path.is_dir():
                    logger.debug(f"Skipping {service_path} as it is not a directory.")
                    continue

                compose_path = service_path / 'docker-compose.yaml'
                if not compose_path.exists():
                    compose_path = service_path / "docker-compose.yml"
                    if not compose_path.exists():
                        logger.error(f"docker-compose file not found for {self.name}/{service_path.name} at {compose_path}. Skipping.")
                        continue

                # Step 3: Load compose YAML
                try:
                    with open(compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)
                except Exception as e:
                    logger.error(f"Error reading {compose_path.name}: {e}")
                    continue

                # Step 4: Check x-spiri-sdk-autostart
                if compose_data.get("x-spiri-sdk-autostart", True):
                    logger.info(f"Autostarting: {self.name}/{service_path.name}")
                    # Step 5: Run `docker compose up -d` inside the DinD container
                    inside_path = f"/robots/{self.robot_type}/services/{service_path.name}"
                    command = f"docker compose --env-file=/data/config.env -f {inside_path}/{compose_path.name} up -d"
                    result = await run.io_bound(lambda r=self.name, c=command, i=inside_path: robots[r].container.exec_run(c, workdir=i))
                    logger.debug(result.output.decode())

        except Exception as e:
            return f"Error starting services for {self.name}: {str(e)}"
        
    def sync_add_to_system(self, selected_options: dict) -> None:
        """Save the robot's configuration to the system for future use."""
        folder_path = SDK_ROOT / 'data' / self.name
        folder_path.mkdir(parents=True, exist_ok=True)
        config_path = folder_path / 'config.env'
        if not config_path.exists():
            with open(config_path, 'w') as f:
                f.write("# Config File\n")
        for key, value in selected_options.items():
            self.set_env(str(key), str(value))
                
    def sync_remove_from_system(self) -> None:
        """Remove the robot from the system."""
        logger.info(f"Deleting robot {self.name}")
        robot_path = SDK_ROOT / 'data' / self.name
        if robot_path.exists():
            shutil.rmtree(robot_path)
        logger.success(f"Robot {self.name} deleted successfully")