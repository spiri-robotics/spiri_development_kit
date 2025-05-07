import docker
import atexit
import subprocess
class DockerInDocker:
    def __init__(self, image_name="docker:dind", container_name="dind"):
        """Initialize the Docker-in-Docker manager.

        Args:
            image_name: Docker image to use (default: docker:dind)
            container_name: Name for the container (default: dind)
            host_port: Host port to bind to (default: None = auto-select)
        """
        self.client = docker.from_env()
        self.image_name = image_name
        self.container_name = container_name
        self.container = None

        # Register cleanup on exit
        atexit.register(self.cleanup)

    def container_ip(self):
        """Get the IP address of the Docker-in-Docker container."""
        if self.container is None:
            raise RuntimeError("Container not running")

        return self.container.attrs['NetworkSettings']['IPAddress']

    def start(self):
        """Start the Docker-in-Docker container."""
        if self.container is not None:
            raise RuntimeError("Container already running")

        self.container = self.client.containers.run(
            self.image_name,
            name=self.container_name,
            privileged=True,
            detach=True,
            remove=True,
            environment={
                'DOCKER_TLS_CERTDIR': ''  # Disable TLS for simplicity
            }
        )
        # Wait for the container to be ready
        while True:
            try:
                self.client.ping()
                break
            except docker.errors.NotFound:
                pass
            except docker.errors.APIError:
                pass

        return self.container

    def get_client(self):
        """Get a Docker client connected to the DinD container."""
        if self.container is None:
            raise RuntimeError("Container not running")

        port = self.host_port or 2376
        docker_host = f"tcp://{self.container_ip()}"

    def cleanup(self):
        """Stop and remove the container."""
        if self.container is not None:
            try:
                self.container.stop()
                self.container.remove()
                self.container = None
            except Exception as e:
                print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Example usage
    dind = DockerInDocker()
    dind.start()
    client = dind.get_client()
    #Run robots/webapp-example/services/whoami/docker-compose.yaml in the remote docker using docker compose
    compose_file = "robots/webapp-example/services/whoami/docker-compose.yaml"
    docker_host = client.api.base_url

    subprocess.run(["docker-compose", "-H", docker_host, '-f', compose_file, "up", "-d"])