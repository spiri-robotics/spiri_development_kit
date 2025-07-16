from pathlib import Path
from loguru import logger
import docker
import dotenv

from spiriSdk.utils import Robot
from gazebo_utils import get_running_worlds, Model
from spiriSdk.pages.tools import gz_world

class DockerRobot(Robot):
    """
    An example implementation of the robot class.
    This docker robot would be running directly off the host machine's docker daemon.
    """
    
    def __init__(self, name: str, folder: Path = Path("/services/")):
        """
        Initialize a DockerRobot instance.
        
        param name: The name of the robot, of the format <robot_type>_<sys_id>.
        param folder: The folder where the robot's services are located.
        This folder should contain a docker-compose.yml file to start the robot's services.
        """
        self.name = name
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.services_folder : Path = folder
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        self.start_services()

    def delete(self) -> None:
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

    def get_status(self) -> str:
        """Get the status of the robot's Docker container."""
        if self.docker_client is None:
            return 'not created or removed'
        try:
            client = docker.DockerClient(base_url=self.connection_url)
            states = {
                "Running": len(client.containers.list(filters={'status': 'running'})),
                "Restarting": len(client.containers.list(filters={'status': 'restarting'})),
                "Exited": len(client.containers.list(filters={'status': 'exited'})),
                "Created": len(client.containers.list(filters={'status': 'created'})),
                "Paused": len(client.containers.list(filters={'status': 'paused'})),
                "Dead": len(client.containers.list(filters={'status': 'dead'})),
            }
            if all(count == 0 for count in states.values()):
                return 'Stopped'
            else:
                return states
        except Exception as e:
            return 'Loading...'
        except docker.errors.NotFound:
            return 'stopped'
        except Exception as e:
            return f'error: {str(e)}'

    def get_env(self) -> dict:
        """Get the environment variables for the robot."""
        return dotenv.dotenv_values(self.folder / 'config.env')

    def set_env(self, key: str, value: str) -> None:
        """Set an environment variable for the robot."""
        dotenv.set_key(self.folder / 'config.env', key, value)
    
    def start_services(self) -> None:
        """Start the robot's services using Docker Compose."""
        for service in self.folder.iterdir():
            if service.is_dir() and (service / 'docker-compose.yml').exists():
                try:
                    compose_file = service / 'docker-compose.yml'
                    self.docker_client.compose.up(compose_file, detach=True)
                except Exception as e:
                    logger.error(f"Error starting services for {service.name}: {str(e)}")
            elif service.is_dir() and (service / 'docker-compose.yaml').exists():
                try:
                    compose_file = service / 'docker-compose.yaml'
                    self.docker_client.compose.up(compose_file, detach=True)
                except Exception as e:
                    logger.error(f"Error starting services for {service.name}: {str(e)}")
            else:
                logger.info(f"No docker-compose file found in {service.name}, skipping.")
    
    def stop_services(self) -> None:
        """Stop the robot's services using Docker Compose."""
        for service in self.folder.iterdir():
            if service.is_dir() and (service / 'docker-compose.yml').exists():
                try:
                    compose_file = service / 'docker-compose.yml'
                    self.docker_client.compose.down(compose_file, remove_images=True)
                except Exception as e:
                    logger.error(f"Error stopping services for {service.name}: {str(e)}")
            elif service.is_dir() and (service / 'docker-compose.yaml').exists():
                try:
                    compose_file = service / 'docker-compose.yaml'
                    self.docker_client.compose.down(compose_file, remove_images=True)
                except Exception as e:
                    logger.error(f"Error stopping services for {service.name}: {str(e)}")
            else:
                logger.info(f"No docker-compose file found in {service.name}, skipping.")

    async def spawn(self) -> bool:
        """Spawn the robot in the Gazebo world."""
        try:
            robotType = "_".join(str(self.name).split('_')[0:-1])
            model = Model(self, self.name, robotType, '127.0.0.1', self.docker_client)
            await model.launch_model()
            gz_world.models.update({self.name:model})
            running_worlds = get_running_worlds()
            if len(running_worlds) > 0:
                logger.info(f'Added {self.name} to world')
                return True
            else:
                raise Exception('No world running')
        except Exception as e:
            logger.warning(f'Failed to spawn {self.name}: {str(e)}')
            return False

    def unspawn(self) -> bool:
        """Unspawn the robot from the Gazebo world."""
        try:
            gz_world.models[self.name].kill_model()
            logger.info(f'Removed {self.name} from world')
            return True
        except Exception as e:
            logger.warning(f'Failed to remove {self.name} from world: {str(e)}')
            return False
