from pathlib import Path
import docker

from spiriSdk.utils import Robot

class DockerRobot(Robot):
    def __init__(self, name: str):
        self.name = name
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.folder: Path | None = None
        self.save_to_system()
        self.start()
        
        #somthing to show started
        
        self.start_services()

    def start(self):
        pass

    def stop(self):
        self.docker_client.close()

    def remove(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_ip(self):
        return "127.0.0.1"

    def get_status(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_env(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def set_env(self, env_vars: dict):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def save_to_system(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def delete_from_system(self):
        pass
    
    def start_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")   
    
    def run_compose(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def spawn(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def unspawn(self):
        raise NotImplementedError("This method should   be implemented by subclasses.")
