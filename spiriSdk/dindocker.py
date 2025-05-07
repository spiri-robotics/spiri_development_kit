import docker
import atexit

class DockerInDocker:
    def __init__(self, image_name="docker:dind", container_name="dind", host_port=None):
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

    def start(self):
        """Start the Docker-in-Docker container."""
        if self.container is not None:
            raise RuntimeError("Container already running")

        port_bindings = {'2376/tcp': self.host_port} if self.host_port else None
        
        self.container = self.client.containers.run(
            self.image_name,
            name=self.container_name,
            privileged=True,
            detach=True,
            remove=True,
            ports=port_bindings,
            environment={
                'DOCKER_TLS_CERTDIR': ''  # Disable TLS for simplicity
            }
        )
        return self.container

    def get_client(self):
        """Get a Docker client connected to the DinD container."""
        if self.container is None:
            raise RuntimeError("Container not running")

        port = self.host_port or 2376
        return docker.DockerClient(base_url=f"tcp://localhost:{port}")

    def cleanup(self):
        """Stop and remove the container."""
        if self.container is not None:
            try:
                self.container.stop()
                self.container.remove()
                self.container = None
            except Exception as e:
                print(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

