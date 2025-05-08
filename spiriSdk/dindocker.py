import docker
import atexit
import subprocess
import time
from typing import Optional

class DockerInDocker:
    def __init__(self, image_name: str = "docker:dind", container_name: str = "dind"):
        """Initialize the Docker-in-Docker manager.

        Args:
            image_name: Docker image to use (default: docker:dind)
            container_name: Name for the container (must be unique per daemon)
        """
        self.client = docker.from_env()
        self.image_name = image_name
        self.container_name = container_name
        self.container: Optional[docker.models.containers.Container] = None
        atexit.register(self.cleanup)

    def container_ip(self) -> str:
        """Get the IP address of the Docker-in-Docker container."""
        if self.container is None:
            raise RuntimeError("Container not running")
        
        ip = self.container.attrs['NetworkSettings']['IPAddress']
        if not ip:
            raise RuntimeError("Container has no IP address assigned")
        return ip

    def start(self) -> None:
        """Start the Docker-in-Docker container."""
        if self.container is not None:
            raise RuntimeError("Container already running")

        try:
            self.container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                privileged=True,
                detach=True,
                remove=True,
                environment={'DOCKER_TLS_CERTDIR': ''},
                publish_all_ports=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {str(e)}")

        # Wait for the container to be ready
        max_attempts = 30
        last_error = None
        for attempt in range(max_attempts):
            try:
                # Get fresh container info
                self.container = self.client.containers.get(self.container.id)
                if self.container.status != 'running':
                    last_error = f"Container status: {self.container.status}"
                    time.sleep(1)
                    continue

                # Check if Docker daemon is ready
                try:
                    client = docker.DockerClient(base_url=f"tcp://{self.container_ip()}:2375")
                    client.ping()
                    return
                except Exception as e:
                    last_error = f"Docker daemon not ready: {str(e)}"
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                time.sleep(1)
        
        # If we get here, all attempts failed
        raise RuntimeError(
            f"Failed to start Docker-in-Docker container after {max_attempts} attempts. "
            f"Last error: {last_error}"
        )

    def get_client(self) -> docker.DockerClient:
        """Get a Docker client connected to this DinD container."""
        if self.container is None:
            raise RuntimeError("Container not running")
        return docker.DockerClient(base_url=f"tcp://{self.container_ip()}:2375")

    def run_compose(self, compose_file: str) -> None:
        """Run a docker-compose file against this DinD instance."""
        client = self.get_client()
        # Ensure we use the correct tcp:// protocol
        docker_host = client.api.base_url.replace('http://', 'tcp://')
        subprocess.run([
            "docker-compose",
            "-H", docker_host,
            "-f", compose_file,
            "up", "-d"
        ], check=True)

    def cleanup(self) -> None:
        """Cleanup handler (still registered but minimal since remove=True handles it)."""
        if self.container is not None:
            try:
                # Just ensure container is stopped - removal is handled by remove=True
                self.container.stop(timeout=5)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception as e:
                print(f"Error during cleanup: {e}")
            self.container = None

if __name__ == "__main__":
    # Example usage
    daemon = DockerInDocker(container_name="dind_test")
    daemon.start()
    
    print(f"Docker-in-Docker IP: {daemon.container_ip()}")
    
    # Verify Docker connection
    client = daemon.get_client()
    print("Docker version:", client.version())
    
    # Run the compose file
    compose_path = "robots/webapp-example/services/whoami/docker-compose.yaml"
    print(f"Running compose file: {compose_path}")
    daemon.run_compose(compose_path)
    
    # List running containers
    print("Running containers:")
    for container in client.containers.list():
        print(f"- {container.name} (ID: {container.short_id})")
    
    # Check if port 80 is listening
    import requests
    try:
        response = requests.get(f"http://{daemon.container_ip()}", timeout=5)
        print(f"Service is running on port 80! Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
    except Exception as e:
        print(f"Failed to connect to port 80: {str(e)}")
