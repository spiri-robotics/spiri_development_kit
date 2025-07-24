from pathlib import Path
from loguru import logger
import docker
import dotenv
import subprocess
import asyncio

from spiriSdk.utils.Robot import Robot
from spiriSdk.utils.gazebo_utils import get_running_worlds, Model
from spiriSdk.pages.tools import gz_world
class DockerRobot(Robot):
    """
    An example implementation of the robot class.
    This docker robot would be running directly off the host machine's docker daemon.
    """
    
    def __init__(self, name: str, services_folder: Path = Path("/services/")):
        """
        Initialize a DockerRobot instance.
        
        param name: The name of the robot, of the format <robot_type>_<sys_id>.
        param services_folder: The services_folder where the robot's services are located.
        This folder should contain a docker-compose.yml file to start the robot's services.
        """
        self.name = name
        self.robot_type = "-".join(self.name.split('-')[:-1])
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.services_folder : Path = services_folder
        self.env_path : Path = self.services_folder / 'config.env'
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        self.start_services()

    def sync_delete(self) -> None:
        """Delete the robot's Docker container and clean up resources."""
        self.stop_services()
        if self.docker_client is not None:
            try:
                self.docker_client.close()
            except Exception as e:
                logger.error(f"Error closing Docker client: {str(e)}")
        if self.spawned:
            self.unspawn()
        self.spawned = False
        self.running = False
        
    def get_ip(self) -> str:
        """Get the IP address of the robot."""
        return "127.0.0.1"

    def sync_get_status(self) -> str | dict:
        """Get the status of the robot's Docker containers."""
        if self.docker_client is None:
            return 'not created or removed'
        try:
            client = self.docker_client
            status_counts = {
                "Running": 0,
                "Restarting": 0,
                "Exited": 0,
                "Created": 0,
                "Paused": 0,
                "Dead": 0
            }
            # Iterate over each sub-service
            for service in self.services_folder.iterdir():
                if not service.is_dir():
                    continue
                if not (service / 'docker-compose.yml').exists() and not (service / 'docker-compose.yaml').exists():
                    continue
                project_name = service.name.replace("_", "-")
                for status in status_counts:
                    containers = client.containers.list(
                        all=True,
                        filters={
                            'status': status.lower(),
                            'label': f'com.docker.compose.project={project_name}'
                        }
                    )
                    status_counts[status] += len(containers)
            if all(count == 0 for count in status_counts.values()):
                return 'Stopped'
            else:
                return status_counts
        except docker.errors.NotFound:
            return 'stopped'
        except Exception as e:
            return f'error: {str(e)}'

    def get_env(self) -> dict:
        """Get the environment variables for the robot."""
        return dotenv.dotenv_values(self.env_path)

    def set_env(self, key: str, value: str) -> None:
        """Set an environment variable for the robot."""
        dotenv.set_key(self.env_path, key, value)
    
    def sync_start_services(self) -> None:
        """Start the robot's services using Docker Compose."""
        for service in self.services_folder.iterdir():
            if service.is_dir() and ((service / 'docker-compose.yml').exists() or (service / 'docker-compose.yaml').exists()):
                try:
                    subprocess.run(
                        ["docker", "compose", "--env-file", str(self.env_path), "up", "-d"],
                        cwd=str(service),
                        check=True
                    )
                    self.running = True
                except Exception as e:
                    logger.error(f"Error starting services for {service.name}: {str(e)}")
    
    def sync_stop_services(self) -> None:
        """Stop the robot's services using Docker Compose."""
        for service in self.services_folder.iterdir():
            if service.is_dir():
                compose_file = None
                if (service / 'docker-compose.yml').exists():
                    compose_file = service / 'docker-compose.yml'
                elif (service / 'docker-compose.yaml').exists():
                    compose_file = service / 'docker-compose.yaml'
                else:
                    logger.info(f"No docker-compose file found in {service.name}, skipping.")
                    continue

                try:
                    # Stop containers using subprocess
                    subprocess.run(
                        ["docker", "compose", "-f", str(compose_file), "down", "--remove-orphans"],
                        cwd=str(service),
                        check=True
                    )

                    # Wait until all containers in this project are gone
                    project_name = service.name.replace("_", "-")
                    while True:
                        containers = self.docker_client.containers.list(all=True, filters={"label": f"com.docker.compose.project={project_name}"})
                        if not any(c.status in {"running", "created", "restarting"} for c in containers):
                            break
                        logger.info(f"Waiting for containers of {project_name} to stop...")
                        asyncio.sleep(1)

                    logger.info(f"All containers for {project_name} have stopped.")
                except Exception as e:
                    logger.error(f"Error stopping services for {service.name}: {str(e)}")

    async def sync_spawn(self) -> bool:
        """Spawn the robot in the Gazebo world."""
        try:
            robotType = "_".join(str(self.name).split('_')[0:-1])
            model = Model(gz_world, self.name, robotType, sys_id=int(self.get_env().get('MAVLINK_SYS_ID', 1)))
            await model.launch_model()
            gz_world.models.update({self.name:model})
            running_worlds = get_running_worlds()
            if len(running_worlds) > 0:
                logger.info(f'Added {self.name} to world')
                self.spawned = True
                return True
            else:
                raise Exception('No world running')
        except Exception as e:
            logger.warning(f'Failed to spawn {self.name}: {str(e)}')
            return False

    def sync_unspawn(self) -> bool:
        """Unspawn the robot from the Gazebo world."""
        try:
            gz_world.models[self.name].kill_model()
            logger.info(f'Removed {self.name} from world')
            self.speawned = False
            return True
        except Exception as e:
            logger.warning(f'Failed to remove {self.name} from world: {str(e)}')
            return False
