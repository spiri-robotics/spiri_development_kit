import docker
import atexit
import subprocess
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any

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
        sdk_root = os.environ.get('SDK_ROOT', '.')
        self.robot_data_root = Path(sdk_root) / "robot_data" / container_name
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
                publish_all_ports=True,
                volumes={
                    str(self.robot_data_root.resolve()): {  # Convert to absolute path
                        'bind': '/data',
                        'mode': 'rw'
                    }
                }
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

    def _prepare_service_paths(self, compose_file: str) -> Dict[str, Any]:
        """Prepare paths for compose file services."""
        compose_path = Path(compose_file)
        service_name = compose_path.parent.name
        
        return {
            'host_path': str(self.robot_data_root / service_name),
            'container_path': f"/data/{service_name}",
            'compose_file': str(compose_path),
            'project_dir': f"/data/{service_name}"  # Add project directory in container
        }

    def run_compose(self, compose_file: str) -> None:
        """Run a docker-compose file against this DinD instance with proper path mapping."""
        paths = self._prepare_service_paths(compose_file)
        client = self.get_client()
        
        # Ensure we use the correct tcp:// protocol
        docker_host = client.api.base_url.replace('http://', 'tcp://')
        
        # Set environment variables for path mapping
        env = os.environ.copy()
        env.update({
            'DOCKER_HOST': docker_host,
            'HOST_DATA_DIR': paths['host_path'],
            'CONTAINER_DATA_DIR': paths['container_path']
        })
        
        subprocess.run([
            "docker-compose",
            "-H", docker_host,
            "-f", paths['compose_file'],
            "--project-directory", paths['project_dir'],  # Use container path
            "up", "-d"
        ], check=True, env=env)

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
    
    # Verify directory was created and inspect mounts
    test_dir = Path("./robot_data/dind_test/whoami/test")
    if test_dir.exists():
        print(f"✓ Directory created: {test_dir}")
    else:
        print(f"✗ Directory not found: {test_dir}")
    
    # Inspect container mounts
    whoami_container = client.containers.get('whoami-whoami-1')
    print("\nContainer mount points:")
    for mount in whoami_container.attrs['Mounts']:
        print(f"- Source: {mount.get('Source', 'N/A')}")
        print(f"  Destination: {mount.get('Destination', 'N/A')}")
        print(f"  Type: {mount.get('Type', 'N/A')}")
        print(f"  RW: {mount.get('RW', 'N/A')}")
    
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
