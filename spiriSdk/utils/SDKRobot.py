from pathlib import Path
from loguru import logger
import docker
import shutil

from spiriSdk.utils.DockerRobot import DockerRobot
from spiriSdk.settings import SDK_ROOT

class SDKRobot(DockerRobot):
    """
    An example implementation of the robot class.
    This docker robot would be running directly off the host machine's docker daemon.
    """
    
    def __init__(self, name: str, services_folder: Path = Path("/services/"), selected_options: dict = None):
        """
        Initialize a DockerRobot instance.
        
        param name: The name of the robot, of the format <robot_type>_<sys_id>.
        param folder: The folder where the robot's services are located.
        This folder should contain a docker-compose.yml file to start the robot's services.
        """
        self.name = name
        self.robot_type = "-".join(self.name.split('-')[:-1])
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.services_folder : Path = services_folder
        self.env_path : Path = SDK_ROOT / 'data' / self.name / 'config.env'
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        if selected_options is not None:
            self.add_to_system()
            for key, value in selected_options.items():
                self.set_env(str(key), str(value))
        
    def start(self) -> None:
        """Start the robot."""
        self.start_services()

    def stop(self) -> None:
        """Stop the robot."""
        self.stop_services()
        
    def restart(self) -> None:
        """Restart the robot."""
        self.stop_services()
        self.start_services()
        
    def delete(self) -> None:
        """Delete the robot's system files and clean up resources."""
        self.stop_services()
        self.remove_from_system()
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
        """Get the status of the robot."""
        return super().get_status()

    def get_env(self) -> dict:
        """Get the environment variables for the robot."""
        return super().get_env()

    def set_env(self, key: str, value: str) -> None:
        """Set the environment variables for the robot."""
        super().set_env(key, value)
    
    def start_services(self) -> None:
        """Start the robot's services using Docker Compose."""
        super().start_services()
    
    def stop_services(self) -> None:
        """Stop the robot's services using Docker Compose."""
        super().stop_services()

    async def spawn(self) -> bool:
        """Spawn the robot in the Gazebo world."""
        return super().spawn()

    def unspawn(self) -> bool:
        """Unspawn the robot from the Gazebo world."""
        return super().unspawn()
        
    def add_to_system(self) -> None:
        folder_path = SDK_ROOT / 'data' / self.name
        folder_path.mkdir(parents=True, exist_ok=True)
        config_path = folder_path / 'config.env'
        if not config_path.exists():
            with open(config_path, 'w') as f:
                f.write("# Config File\n")

    def remove_from_system(self) -> None:
        """Remove the robot from the system."""
        logger.info(f"Deleting robot {self.name}")
        robot_path = SDK_ROOT / 'data' / self.name
        if robot_path.exists():
            shutil.rmtree(robot_path)
        logger.success(f"Robot {self.name} deleted successfully")