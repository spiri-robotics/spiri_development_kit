"""
Container management classes including base Container and DockerInDocker implementations.
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


from dataclasses import dataclass, field

CURRENT_PRIMARY_GROUP = os.getgid()

@dataclass
class Container:
    """Base container management class with common functionality."""
    
    image_name: str
    container_name: str = field(default_factory=lambda: f"container_{uuid.uuid4().hex[:8]}")
    client: docker.DockerClient = field(default_factory=docker.from_env, init=False)
    container: Optional[docker.models.containers.Container] = field(default=None, init=False)
    privileged: bool = field(default=False)
    auto_remove: bool = field(default=True)
    volumes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, Optional[int]] = field(default_factory=dict)
    ready_timeout: int = field(default=30)
    sdk_root: Path = field(default_factory=lambda: Path(os.environ.get("SDK_ROOT", ".")).resolve())
    command: Optional[str] = field(default=None)
    entrypoint: Optional[str] = field(default=None)

    def __post_init__(self):
        """Register cleanup handler after initialization."""
        atexit.register(self.cleanup)
        # Ensure cache directory exists
        cache_dir = Path(os.environ.get("SDK_ROOT", ".")) / "cache" / "certs"
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Ensure all volume paths are absolute
        self.volumes = {
            str(Path(src).resolve()): bind for src, bind in self.volumes.items()
        }

    def ensure_started(self) -> None:
        """Ensure container is running, starting it if needed.

        Raises:
            RuntimeError: If container fails to start
        """

        print(self.container)
        
        try:
            # Check if a container with the same name already exists
            if self.container is None:
                print(f"Container name: {self.container_name}")
                existing_containers = self.client.containers.list(all=True, filters={"name": self.container_name})
                if existing_containers:
                    self.container = existing_containers[0]
                    if self.container.status == "running":
                        print(f"Container {self.container_name} is already running.")
                        return
                    else:
                        print(f"Starting existing container {self.container_name}.")
                        self.container.start()
                        return
                else:
                    logger.info(f"Starting container {self.container_name} using image {self.image_name}")
                
                    docker_args = {
                        "image": self.image_name,
                        "name": self.container_name,
                        "privileged": self.privileged,
                        "detach": True,
                        "remove": self.auto_remove,
                        "environment": self.environment,
                        "ports": self.ports,
                        "volumes": self.volumes,
                    }
                    if self.command is not None:
                        docker_args["command"] = self.command
                    if self.entrypoint is not None:
                        docker_args["entrypoint"] = self.entrypoint

                    self.container = self.client.containers.run(**docker_args)
            else:
                try:
                    self.container.reload()
                    if self.container.status != "running":
                        print(f"Starting container {self.container_name}...")
                        self.container.start()
                    else:
                        print(f"Container {self.container_name} is already running.")
                        return
                except docker.errors.NotFound:
                    print(f"Container {self.container_name} not found (probably auto-removed). Recreating...")
                    self.container = None
                    return self.ensure_started()  # retry from beginning
        except docker.errors.NotFound:
                    print(f"Container {self.container_name} not found (probably auto-removed). Recreating...")
                    self.container = None
                    return self.ensure_started()  # retry from beginning
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {str(e)}")

        logger.debug("Waiting for container to be ready...")
        # Wait for container to be ready
        for attempt in range(self.ready_timeout):
            try:
                # Get fresh container info
                self.container = self.client.containers.get(self.container.id)
                if self.container.status != "running":
                    time.sleep(1)
                    continue
                return
            except Exception:
                time.sleep(1)

        raise RuntimeError(
            f"Failed to start container after {self.ready_timeout} attempts"
        )

    def __enter__(self):
        """Context manager entry point."""
        self.ensure_started()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
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

    def cleanup(self) -> None:
        """Clean up container resources."""
        if self.container is not None:
            try:
                self.container.stop(timeout=5)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            self.container = None

@dataclass
class DockerRegistryProxy(Container):
    """This is a hack as currently there's no good way to cache pulls from
    multiple types of registries.
    """
    image_name: str = "rpardini/docker-registry-proxy:0.6.5"
    container_name: str = field(default_factory=lambda: f"registry_proxy_{uuid.uuid4().hex[:8]}")

    environment: Dict[str, str] = field(
        default_factory=lambda: {
            "GENERATE_MIRRORING_CA": "true",  # Ensure CA cert is generated
            "DISABLE_IPV6": "true",  # Disable IPv6
        }
    )
    volumes: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            str(Path(os.environ.get("SDK_ROOT", ".")) / "cache" / "certs"): {"bind": "/certs", "mode": "rw"}
        }
    )

    def get_cacert(self) -> str:
        """Get the CA certificate for the registry mirror.

        Returns:
            str: The CA certificate contents from fullchain.pem
        """
        if self.container is None:
            raise RuntimeError("Container not running")
        
        # Wait for cert to be generated (max 120 seconds)
        for attempt in range(120):
            result = self.container.exec_run("cat /certs/fullchain.pem")
            if result.exit_code == 0:
                cert = result.output.decode("utf-8").strip()
                if cert:  # Only return if we got non-empty content
                    return cert
            
            # Additional debug info
            if attempt % 5 == 0:  # Every 5 seconds
                print(f"Attempt {attempt}, waiting for certificate...")
                print(f"Cert dir contents:\n{self.container.exec_run('ls -la /certs').output.decode()}")
            
            time.sleep(1)
        
        raise RuntimeError(
            f"Certificate not generated after 30 seconds.\n"
            f"Cert dir contents:\n{self.container.exec_run('ls -la /certs').output.decode()}"
        )

DEFAULT_REGISTRY_PROXY = DockerRegistryProxy()

@dataclass
class DockerInDocker(Container):
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

    image_name: str = "docker:dind"
    socket_dir: Path = field(default_factory=lambda: Path("/tmp/dind-sockets"))

    container_name: str = field(default_factory=lambda: f"dind_{uuid.uuid4().hex[:8]}")
    privileged: bool = field(default=True, init=False)
    environment: Dict[str, str] = field(
        default_factory=lambda: {
           #"DOCKER_TLS_CERTDIR": ""

                                 
            },  # Disable TLS
        init=False
    )
    ports: Dict[str, Optional[int]] = field(
        default_factory=lambda: {"2375/tcp": None},  # Publish Docker port
        init=False
    )
    robot_data_root: Path = field(init=False)
    #registry_proxy: Optional[DockerRegistryProxy] = field(default_factory=lambda: DEFAULT_REGISTRY_PROXY)
    registry_proxy: Optional[DockerRegistryProxy] = field(default=None)

    def __post_init__(self):
        """Initialize DinD-specific paths and settings."""
        super().__post_init__()
        self.robot_data_root = self.sdk_root / "data" / self.container_name
        self.robot_data_root.mkdir(parents=True, exist_ok=True)
        
        # Create socket directory if it doesn't exist
        self.socket_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        
        self.volumes.update({
            str(self.robot_data_root): {"bind": "/data", "mode": "rw"},
            str(self.socket_dir): {"bind": "/dind-sockets", "mode": "rw"}
        })
        self.command = [
            f'--host=unix:///dind-sockets/{self.container_name}.socket'
        ]


    def ensure_started(self) -> None:
        """Start the Docker-in-Docker container with specialized configuration."""
        if self.container is not None:
            # Container already running
            return

        # Debug: Verify volumes before starting
        logger.debug(f"Volume mounts before start: {self.volumes}")
        if not self.socket_dir.exists():
            logger.error(f"Host directory {self.socket_dir} does not exist!")
            self.socket_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
            
        if self.registry_proxy:
            self.registry_proxy.ensure_started()
            # Get CA cert from proxy and store it in robot_data_root
            ca_cert = self.registry_proxy.get_cacert()
            cert_path = self.robot_data_root / "ca.crt"
            with open(cert_path, 'w') as f:
                f.write(ca_cert)
            
            # Add volume for the CA cert
            self.volumes.update({
                str(cert_path): {"bind": "/usr/local/share/ca-certificates/registry-ca.crt", "mode": "ro"}
            })

            # Set proxy environment variables
            proxy_ip = self.registry_proxy.container_ip()
            self.environment.update({
                "HTTP_PROXY": f"http://{proxy_ip}:3128",
                "HTTPS_PROXY": f"http://{proxy_ip}:3128",
                "NO_PROXY": "localhost,127.0.0.1"
            })

        super().ensure_started()  # Use base class implementation


        if self.registry_proxy:
            # Update CA certificates in the DinD container
            self.container.exec_run("update-ca-certificates")

        # Additional DinD-specific readiness check
        logger.debug("Checking Docker daemon readiness...")
        for attempt in range(self.ready_timeout):
            try:
                # Set ownership and permissions of socket file inside container
                socket_path = f"/dind-sockets/{self.container_name}.socket"
                self.container.exec_run(f"chown :{CURRENT_PRIMARY_GROUP} /dind-sockets/{self.container_name}.socket")
                self.container.exec_run(f"chmod 666 /dind-sockets/{self.container_name}.socket")
                
                self.get_client().ping()
                logger.success("Docker-in-Docker container started successfully")
                return
            except Exception as e:
                if attempt == self.ready_timeout - 1:
                    raise RuntimeError(
                        f"Docker daemon not ready after {self.ready_timeout} attempts: {str(e)}"
                    )
                time.sleep(1)

    def get_client(self) -> docker.DockerClient:
        """Get a Docker client connected to this DinD container."""
        if self.container is None:
            raise RuntimeError("Container not running")
        return docker.DockerClient(base_url=f"unix:///tmp/dind-sockets/{self.container_name}.socket")
        #return docker.DockerClient(base_url=f"tcp://{self.container_ip()}:2375")

    def _prepare_service_paths(self, compose_file: str) -> Dict[str, Any]:
        """Prepare path mappings for a compose file service.

        Args:
            compose_file: Path to docker-compose.yaml file

        Returns:
            Dict with paths for host, container, compose file and project dir
        """
        compose_path = Path(compose_file)
        service_name = compose_path.parent.name
        host_path = self.robot_data_root / service_name

        return {
            "host_path": str(host_path),
            "container_path": f"/data/{service_name}",
            "compose_file": str(compose_path),
            "project_dir": f"/data/{service_name}",  # Project dir in container
        }

    def run_compose(self, compose_file: str, max_attempts: int = 3) -> None:
        """Run docker compose with retry logic for network issues.
        
        Args:
            compose_file: Path to docker-compose.yaml file
            max_attempts: Maximum number of retry attempts (default: 3)

        Raises:
            RuntimeError: If compose fails after all retry attempts
        """
        logger.info(f"Running compose file: {compose_file}")
        
        paths = self._prepare_service_paths(compose_file)
        client = self.get_client()
        docker_host = f"unix://{self.socket_dir}/{self.container_name}.socket"
        logger.debug(f"Docker host: {docker_host}")
        env = os.environ.copy()
        env.update({
            "DOCKER_HOST": docker_host,
            "HOST_DATA_DIR": paths["host_path"],
            "CONTAINER_DATA_DIR": paths["container_path"]
        })

        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "--file", paths["compose_file"],
                        "--project-directory", paths["project_dir"],
                        "up",
                        "--detach",
                    ],
                    check=True,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                return
            except subprocess.CalledProcessError as e:
                last_exception = e
                logger.warning(f"Compose attempt {attempt} failed: {e.stderr}")
                if attempt < max_attempts:
                    time.sleep(5)  # Wait before retry

        raise RuntimeError(
            f"Failed to run compose after {max_attempts} attempts. Last error: {str(last_exception)}"
        )

