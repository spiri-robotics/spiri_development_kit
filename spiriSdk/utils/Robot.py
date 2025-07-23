from pathlib import Path
import docker
# use nicegui runiobound for asynchronizing methods
class Robot(object):
    def __init__(self, name: str):
        self.name: str = name
        self.folder : Path | None
        self.docker_client : docker.DockerClient  | None
        self.connection_url: str | None = None
        self.spawned: bool = False
        self.running: bool = False
        
    def sync_delete(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def delete(self):
        return await self.sync_delete()

    def get_ip(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def sync_get_status(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def get_status(self):
        return await self.sync_get_status()

    def get_env(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def set_env(self, env_vars: dict):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def sync_start_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")   
    
    async def start_services(self):
        return await self.sync_start_services()
    
    def sync_stop_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def stop_services(self):
        return await self.sync_stop_services()
    
    def sync_spawn(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    async def spawn(self):
        return await self.sync_spawn()

    def sync_unspawn(self):
        raise NotImplementedError("This method should   be implemented by subclasses.") 
    
    async def unspawn(self):
        return await self.sync_unspawn()
