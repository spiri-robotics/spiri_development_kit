from pathlib import Path
import docker

class Robot(object):
    def __init__(self, name: str):
        self.name: str = name
        self.folder : Path | None
        self.docker_client : docker.DockerClient  | None
        self.connection_url: str | None = None
        self.spawned: bool = False
        self.running: bool = False
        
    def delete(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_ip(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_status(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_env(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def set_env(self, env_vars: dict):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def start_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")   
    
    def stop_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def spawn(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def unspawn(self):
        raise NotImplementedError("This method should   be implemented by subclasses.") 
