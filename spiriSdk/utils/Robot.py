from pathlib import Path
from nicegui import run
import docker
# use nicegui runiobound for asynchronizing methods
# add comments on why you'd use these and how and when and who and where and what
class Robot(object):
    """
    An abstract class representing a robot to be simulated or controlled.

    Args:
        str name: The name of the robot, typically in the format <robot_type>_<sys_id>.
    """
    def __init__(self, name: str):
        self.name: str = name
        self.services_folder : Path | None
        self.env_path: Path | None
        self.docker_client : docker.DockerClient  | None
        self.connection_url: str | None = None
        self.spawned: bool = False
        self.running: bool = False
        
    async def start(self):
        """
        This method should start the robot.
        This includes starting the robot's services, and if applicable, its docker container.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def stop(self):
        """
        This method should stop the robot.
        This includes stopping the robot's services, and if applicable, its docker container.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def restart(self):
        """
        This method should restart the robot.
        It can do so by simply calling stop then start.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def delete(self):
        """
        This method should remove the robot from the system and clean up resources.
        This includes deleting the robot's Docker container and closing the Docker client,
        unspawning the robot if it was spawned into a simulation environment,
        and deleting the config.env and services folder.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_ip(self):
        """
        This method should return the IP at which the robot can be accessed.
        
        Returns:
            str: The IP address of the robot.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def sync_get_status(self):
        """
        This method should return a string with the status of the robot if no services are running,
        or a dictionary with the status of the robot's services if they are running.

        Returns:
            str | dict: The status of the robot, which can be a string or a dictionary.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def get_status(self):
        """
        The asynchronous call of sync_get_status.
        
        This method should return a string with the status of the robot if no services are running,
        or a dictionary with the status of the robot's services if they are running.

        Returns:
            str | dict: The status of the robot, which can be a string or a dictionary.
        """
        return await run.io_bound(self.sync_get_status)

    def get_env(self):
        """
        This method should return the environment variables of the robot as a dictionary
        as they are found in the config.env file at self.env_path.

        Returns:
            dict: The environment variables of the robot.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def set_env(self):
        """
        This method should set an environment variable for the robot in the 
        config.env file at self.env_path.
        
        Args:
            key (str): The name of the environment variable.
            value (str): The value of the environment variable.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def sync_start_services(self):
        """
        This method should start each of the robot's services,
        found in the service_folder each as their own folder with a Docker Compose.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")   
    
    async def start_services(self):
        """
        The asynchronous call of sync_start_services.
        
        This method should start each of the robot's services,
        found in the service_folder each as their own folder with a Docker Compose.
        """
        return await run.io_bound(self.sync_start_services)
    
    def sync_stop_services(self):
        """
        This method should stop each of the robot's services,
        found in the service_folder each as their own folder with a Docker Compose.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def stop_services(self):
        """
        The asynchronous call of sync_stop_services.
        
        This method should stop each of the robot's services,
        found in the service_folder each as their own folder with a Docker Compose.
        """
        return await run.io_bound(self.sync_stop_services)
    
    def sync_spawn(self):
        """
        This method should spawn a model of the robot into a simulation environment.
        In this SDK, we use Gazebo.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def spawn(self):
        """
        The asynchronous call of sync_spawn.
        
        This method should spawn a model of the robot into a simulation environment.
        In this SDK, we use Gazebo.
        """
        return await run.io_bound(self.sync_spawn)

    def sync_unspawn(self):
        """
        This method should unspawn the robot from the simulation environment.
        In this SDK, we use Gazebo.
        """
        raise NotImplementedError("This method should   be implemented by subclasses.") 
    
    async def unspawn(self):
        """
        The asynchronous call of sync_unspawn.
        
        This method should unspawn the robot from the simulation environment.
        In this SDK, we use Gazebo.
        """
        return await run.io_bound(self.sync_unspawn)
    
    def sync_add_to_system(self):
        """
        This method should save the robot's configuration to the system for future use.
        For a local robot this includes creating a folder for the robot in the SDK_ROOT/data directory,
        creating a config.env file in that folder, and writing the robot's configuration to it.

        Args:
            dict selected_options: A dictionary of settings to be saved in the config.env file.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def add_to_system(self, selected_options: dict) -> None:
        """
        The asynchronous call of sync_add_to_system.
        
        This method should save the robot's configuration to the system for future use.
        For a local robot this includes creating a folder for the robot in the SDK_ROOT/data directory,
        creating a config.env file in that folder, and writing the robot's configuration to it. 
        
        Args:
            dict selected_options: A dictionary of settings to be saved in the config.env file.
        """
        return await run.io_bound(self.sync_add_to_system, selected_options)
    
    def sync_remove_from_system(self) -> None:
        """
        This method should remove the robot from the system.
        This means deleting the folder with its name under SDK_ROOT/data if it exists.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")   
    
    async def remove_from_system(self) -> None:
        """
        The asynchronous call of sync_remove_from_system.

        This method should remove the robot from the system.
        This means deleting the folder with its name under SDK_ROOT/data if it exists.
        """
        return await run.io_bound(self.sync_remove_from_system)
