from pathlib import Path
from loguru import logger
from dataclasses import dataclass
import docker
import shutil

from spiriSdk.classes.DockerRobot import DockerRobot
from spiriSdk.settings import SDK_ROOT

@dataclass
class LocalRobot(DockerRobot):
    """
    An implementation of the robot class.
    This docker robot would be running directly off the host machine's docker daemon.
    """
    
    def __init__(self, name: str, services_folder: Path = Path("/services/")):
        """
        Initialize a DockerRobot instance.
        
        param name: The name of the robot, of the format <robot_type>_<sys_id>.
        param folder: The folder where the robot's services are located.
        This folder should contain a docker-compose.yml file to start the robot's services.
        """
        self.name = name
        self.robot_type = "_".join(self.name.split('_')[:-1])
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.services_folder : Path = services_folder
        self.env_path : Path = SDK_ROOT / 'data' / self.name / 'config.env'
        self.docker_host : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False

    async def delete(self) -> None:
        """
        Cleans up resources associated with the robot.
        This includes stopping the robot's services, removing it from the system,
        closing the Docker client, and unspawning the robot if it was spawned 
        into a simulation environment.
        """
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
        return "127.0.0.1"
    
    def get_docker_host(self) -> str:
        """
        This method returns the Docker host for the robot's docker container.
        
        Returns:
            str: The Docker host.
        """
        return super().get_docker_host()
        
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