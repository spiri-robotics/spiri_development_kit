"""
Docker-in-Docker (DinD) manager for running nested Docker containers.

This provides a clean interface to:
- Start/stop a Docker daemon inside a container
- Run docker-compose files against the nested Docker
- Manage data volumes and paths between host and containers
"""

import docker
import atexit
import subprocess
import time
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


class DockerInDocker:
    """Manager for Docker-in-Docker containers with path mapping support.

    Features:
    - Automatic cleanup on exit
    - Path mapping between host and containers
    - Docker compose support
    - SDK_ROOT environment variable integration

    Typical usage:
        with DockerInDocker() as dind:
            dind.run_compose("path/to/compose.yaml")
    """

    def __init__(self, image_name: str = "docker:dind", container_name: str = None):
        """Initialize the Docker-in-Docker manager.

        Args:
            image_name: Docker image to use (default: docker:dind)
            container_name: Optional unique name for this container instance.
                           If None, will use "dind_<test_name>_<pid>"
        """
        # Generate unique container name if not specified
        if container_name is None:
            import uuid
            container_name = f"dind_{uuid.uuid4().hex[:8]}"
        self.client = docker.from_env()
        self.image_name = image_name
        self.container_name = container_name
        self.container: Optional[docker.models.containers.Container] = None

        # Set up paths - use SDK_ROOT if available, otherwise current directory
        sdk_root = os.environ.get("SDK_ROOT", ".")
        self.robot_data_root = Path(sdk_root) / "robot_data" / container_name

        # Ensure cleanup on exit
        atexit.register(self.cleanup)

    def __enter__(self):
        """Context manager entry point - starts the container."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.cleanup()

    def container_ip(self) -> str:
        """Get the container's IP address.

        Returns:
            str: The container's IP address

        Raises:
            RuntimeError: If container isn't running or has no IP
        """
        if self.container is None:
            raise RuntimeError("Container not running")

        ip = self.container.attrs["NetworkSettings"]["IPAddress"]
        if not ip:
            raise RuntimeError("Container has no IP address assigned")
        return ip

    def start(self) -> None:
        """Start the Docker-in-Docker container.

        Sets up:
        - Privileged container with Docker socket
        - Volume mapping for /data directory
        - Automatic removal on stop

        Raises:
            RuntimeError: If container fails to start
        """
        if self.container is not None:
            raise RuntimeError("Container already running")

        logger.info(f"Starting Docker-in-Docker container {self.container_name} using image {self.image_name}")
        try:
            self.container = self.client.containers.run(
                image=self.image_name,
                name=self.container_name,
                privileged=True,
                detach=True,
                remove=True,  # Auto-remove when stopped
                environment={
                    "DOCKER_TLS_CERTDIR": ""  # Disable TLS for simplicity
                },
                publish_all_ports=True,
                volumes={
                    # Map host robot_data to container /data
                    str(self.robot_data_root.resolve()): {"bind": "/data", "mode": "rw"}
                },
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {str(e)}")

        logger.debug("Waiting for container to be ready...")
        # Wait for the container to be ready
        max_attempts = 30
        last_error = None
        for attempt in range(max_attempts):
            try:
                # Get fresh container info
                self.container = self.client.containers.get(self.container.id)
                if self.container.status != "running":
                    last_error = f"Container status: {self.container.status}"
                    time.sleep(1)
                    continue

                # Check if Docker daemon is ready
                try:
                    client = docker.DockerClient(
                        base_url=f"tcp://{self.container_ip()}:2375"
                    )
                    client.ping()
                    logger.success("Docker-in-Docker container started successfully")
                    return
                except Exception as e:
                    last_error = f"Docker daemon not ready: {str(e)}"
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                time.sleep(1)

        logger.error(f"Failed to start container after {max_attempts} attempts")
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
        """Prepare path mappings for a compose file service.

        Args:
            compose_file: Path to docker-compose.yaml file

        Returns:
            Dict with paths for host, container, compose file and project dir
        """
        compose_path = Path(compose_file)
        service_name = compose_path.parent.name
        
        # Ensure parent directory exists with proper permissions first
        self.robot_data_root.mkdir(parents=True, exist_ok=True)
        os.chmod(str(self.robot_data_root), 0o777)  # Make parent writable
        
        # Then create service directory
        host_path = self.robot_data_root / service_name
        try:
            host_path.mkdir(exist_ok=True)
            os.chmod(str(host_path), 0o777)
        except PermissionError:
            # If we still can't create, try with relaxed umask
            old_umask = os.umask(0)
            try:
                host_path.mkdir(exist_ok=True)
                os.chmod(str(host_path), 0o777)
            finally:
                os.umask(old_umask)

        return {
            "host_path": str(host_path),
            "container_path": f"/data/{service_name}",
            "compose_file": str(compose_path),
            "project_dir": f"/data/{service_name}",  # Project dir in container
        }

    def run_compose(self, compose_file: str) -> None:
        logger.info(f"Running compose file: {compose_file}")
        """Run a docker-compose file against the DinD instance.

        Handles:
        - Path mapping between host and container
        - Proper Docker host configuration
        - Project directory setup

        Args:
            compose_file: Path to docker-compose.yaml file

        Raises:
            subprocess.CalledProcessError: If compose fails
            RuntimeError: If DinD container isn't running
        """
        paths = self._prepare_service_paths(compose_file)
        client = self.get_client()

        # Configure Docker host URL
        docker_host = client.api.base_url.replace("http://", "tcp://")

        # Set up environment for compose
        env = os.environ.copy()
        env.update(
            {
                "DOCKER_HOST": docker_host,
                "HOST_DATA_DIR": paths["host_path"],
                "CONTAINER_DATA_DIR": paths["container_path"],
            }
        )

        # Run docker-compose with proper path mappings
        subprocess.run(
            [
                "docker-compose",
                "-H",
                docker_host,
                "-f",
                paths["compose_file"],
                "--project-directory",
                paths["project_dir"],
                "up",
                "-d",
            ],
            check=True,
            env=env,
        )

    def cleanup(self) -> None:
        """Cleanup handler (still registered but minimal since remove=True handles it)."""
        if self.container is not None:
            try:
                # Just ensure container is stopped - removal is handled by remove=True
                self.container.stop(timeout=5)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            self.container = None
