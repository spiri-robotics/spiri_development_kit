from pathlib import Path
import docker
import dotenv

from spiriSdk.utils import Robot

class DockerRobot(Robot):
    def __init__(self, name: str, folder: Path = Path("/services/")):
        self.name = name
        self.docker_client : docker.DockerClient | None = docker.from_env()
        self.services_folder : Path = folder
        self.connection_url : str | None = self.docker_client.api.base_url
        self.spawned: bool = False
        self.running: bool = False
        
        #somthing to show started
        
        self.start_services()

    def delete(self):
        self.remove_from_system()
        
    def get_ip(self):
        return "127.0.0.1"

    def get_status(self):
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
        return dotenv.dotenv_values(self.folder / 'config.env')

    def set_env(self, key: str, value: str) -> None:
        dotenv.set_key(self.folder / 'config.env', key, value)
    
    def start_services(self):
        for service in self.folder.iterdir():
            if service.is_dir() and (service / 'docker-compose.yml').exists():
                try:
                    compose_file = service / 'docker-compose.yml'
                    self.docker_client.compose.up(compose_file, detach=True)
                except Exception as e:
                    print(f"Error starting services for {service.name}: {str(e)}")
    
    def stop_services(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def run_compose(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def spawn(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def unspawn(self):
        raise NotImplementedError("This method should be implemented by subclasses.")
