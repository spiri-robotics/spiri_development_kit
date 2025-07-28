from loguru import logger
from pathlib import Path
import docker
import shutil

from spiriSdk.classes.DockerRobot import DockerRobot
from spiriSdk.docker.dindocker import DockerInDocker
from spiriSdk.settings import SDK_ROOT
class DinDockerRobot(DockerRobot):
    """
    An example implementation of the robot class.
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
        self.robot_type = "-".join(self.name.split('-')[:-1])
        self.services_folder : Path = services_folder
        self.env_path : Path = SDK_ROOT / 'data' / self.name / 'config.env'
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        self.dind = DockerInDocker(name=self.name, services_folder=self.services_folder)
        self.docker_client : docker.DockerClient | None = None
        
    async def start(self) -> None:
        """Starts the robot by starting the dind instance and the services."""
        await self.dind.ensure_started()
        self.docker_client = self.dind.get_docker_client()
        await self.start_services()
        
    async def stop(self) -> None:
        """Stops the robot by stopping the services and the dind instance."""
        await self.stop_services()
        await self.dind.ensure_stopped()
        self.docker_client = None

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
    
    def sync_start_services(self):
        return super().sync_start_services()
    
    def sync_stop_services(self):
        return super().sync_stop_services()
        
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