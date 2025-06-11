"""
Container management classes including base Container and DockerInDocker implementations.
"""

import docker, atexit, subprocess, time, os, uuid, asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from dotenv import load_dotenv
from dataclasses import dataclass, field
import hashlib
import base64
import requests

CURRENT_PRIMARY_GROUP = os.getgid()

def cleanup_docker_resources():
    """Cleanup function to remove all stopped containers and unused images."""
    client = docker.from_env()
    #Find all containers that start with "spirisdk_" and remove them
    containers = client.containers.list(all=True, filters={"name": "spirisdk_"})
    logger.info(f"Cleaning up {len(containers)} containers...")
    for container in containers:
        try:
            logger.info(f"Removing container {container.name} ({container.id})")
            container.remove(force=True)
        except docker.errors.APIError as e:
            logger.error(f"Failed to remove container {container.name}: {e}")

cleanup_docker_resources()

atexit.register(cleanup_docker_resources)

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
        #print(f"Ensuring container {self.container_name} is started with image {self.image_name}")
        try:
            # Check if a container with the same name already exists
            if self.container is None:
                existing_containers = self.client.containers.list(all=True, filters={"name": "spirisdk_"+self.container_name})
                if existing_containers:
                    self.container = existing_containers[0]
                    if self.container.status == "running":
                        logger.info(f"Container spirisdk_{self.container_name} is already running.")
                        return
                    else:
                        logger.info(f"Starting existing container spirisdk_{self.container_name}.")
                        self.container.start()
                        return
                else:
                    logger.info(f"Starting container spirisdk_{self.container_name} using image {self.image_name}")
                    print(f"Starting container spirisdk_{self.container_name} using ports {self.ports}")
                    docker_args = {
                        "image": self.image_name,
                        "name": "spirisdk_"+self.container_name,
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
                        logger.info(f"Starting container spirisdk_{self.container_name}...")
                        self.container.start()
                    else:
                        logger.info(f"Container spirisdk_{self.container_name} is already running.")
                        return
                except docker.errors.NotFound:
                    logger.warning(f"Container spirisdk_{self.container_name} not found (probably auto-removed). Recreating...")
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

    def get_ip(self) -> str:
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
        logger.debug(f"Cleaning up container spirisdk_{self.container_name}")
        if self.container is not None:
            try:
                self.container.stop(timeout=5)
            except docker.errors.NotFound:
                pass  # Container already gone
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            self.container = None

    def inject_file(self, content: str, container_path: str, mode: int = 0o644) -> None:
        """Inject a file with given content into the container.
        
        Args:
            content: String content to write to the file
            container_path: Absolute path where file should be created in container
            mode: File permissions (default: 0o644)
            
        Raises:
            RuntimeError: If container isn't running or injection fails
        """
        if self.container is None:
            raise RuntimeError("Container not running")

        try:
            # Ensure path is absolute
            if not container_path.startswith('/'):
                container_path = f'/{container_path}'

            # Create parent directories if needed
            dir_path = str(Path(container_path).parent)
            self.container.exec_run(f"mkdir -p {dir_path}")
            
            # Create a temporary file with the content
            temp_file = Path(f"/tmp/inject_{uuid.uuid4().hex[:8]}")
            temp_file.write_text(content)
            
            try:
                # Copy file into container
                self.container.put_archive(
                    path="/",  # Always use root as base path
                    data=self._create_tar_archive(temp_file, container_path)
                )
                
                # Set permissions
                self.container.exec_run(f"chmod {oct(mode)[2:]} {container_path}")
            finally:
                temp_file.unlink()  # Clean up temp file
                
        except Exception as e:
            raise RuntimeError(f"Failed to inject file: {str(e)}")

    def _create_tar_archive(self, src_path: Path, dest_path: str) -> bytes:
        """Create a tar archive containing a single file.
        
        Args:
            src_path: Path to source file on host
            dest_path: Destination path in container
            
        Returns:
            bytes: Tar archive data
        """
        import io
        import tarfile
        
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tar.gettarinfo(str(src_path), arcname=dest_path)
            with src_path.open('rb') as f:
                tar.addfile(tarinfo, f)
        
        tar_stream.seek(0)
        return tar_stream.read()

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
    #(pwd)/docker_mirror_cache:/docker_mirror_cache
    volumes: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            str(Path(os.environ.get("SDK_ROOT", ".")) / "cache" / "docker_images"): {"bind": "/docker_mirror_cache", "mode": "rw"},
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
            try:
                response = requests.get(f"http://{self.get_ip()}:3128/ca.crt")  # Ensure the proxy is up
                logger.info('Response received')
                return response.text
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}: Failed to fetch CA cert: {e}")
            
            # Additional debug info
            if attempt % 5 == 0:  # Every 5 seconds
                print(f"Attempt {attempt}, waiting for certificate...")
                print(f"Cert dir contents:\n{self.container.exec_run('ls -la /certs').output.decode()}")
            
            time.sleep(1)
        
        raise RuntimeError(
            f"Certificate not generated after 30 seconds.\n"
            f"Cert dir contents:\n{self.container.exec_run('ls -la /certs').output.decode()}"
        )
    
dotenv_path = Path(".env")
if not dotenv_path.exists():
    dotenv_path.write_text("REGISTRIES=\nAUTH_REGISTRIES=\n")
    logger.info(".env file created with empty REGISTRIES and AUTH_REGISTRIES")    
load_dotenv()
    
creds = {
    "REGISTRIES": os.getenv("REGISTRIES"),
    "AUTH_REGISTRIES": os.getenv("AUTH_REGISTRIES")
}

DEFAULT_REGISTRY_PROXY = DockerRegistryProxy(container_name="registry_proxy")
DEFAULT_REGISTRY_PROXY.environment.update(creds)

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
            "BUILDKIT_HOST": "/var/run/docker-host.sock",  # Use custom socket for BuildKit
            "DOCKER_BUILDKIT": "1",  # Enable BuildKit
            },
        init=False
    )
    ports: Dict[str, Optional[int]] = field(
        default_factory=lambda: {
            "2375/tcp": None},  # Publish Docker port
        init=False
    )
    robot_data_root: Path = field(init=False)
    robot_root: Path = field(init=False)
    robot_type: str = field(init=False)
    registry_proxy: Optional[DockerRegistryProxy] = field(default_factory=lambda: DEFAULT_REGISTRY_PROXY)
    #registry_proxy: Optional[DockerRegistryProxy] = field(default=None)

    def __post_init__(self):
        """Initialize DinD-specific paths and settings."""
        super().__post_init__()
        atexit.register(self.cleanup)
        self.robot_type = "-".join(self.image_name.split('-')[:-1])
        self.robot_data_root = self.sdk_root / "data" / self.container_name
        self.robot_data_root.mkdir(parents=True, exist_ok=True)
        self.robot_root = self.sdk_root / "robots" / self.robot_type
        
        # Create socket directory if it doesn't exist
        self.socket_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        
        self.volumes.update({
            str(self.robot_data_root): {"bind": "/data", "mode": "rw"},
            str(self.socket_dir): {"bind": "/dind-sockets", "mode": "rw"},
            str(self.robot_root): {"bind": f"/robots/{self.robot_type}", "mode": "rw"},
            #Host docker socket
            str("/var/run/docker.sock"): {"bind": "/var/run/docker-host.sock", "mode": "rw"}
        })
                
        self.command = [
            f'--host=unix:///dind-sockets/spirisdk_{self.container_name}.socket'
        ]

    def ensure_started(self) -> None:
        """Start the Docker-in-Docker container with specialized configuration."""
        # Debug: Verify volumes before starting
        logger.debug(f"Volume mounts before start: {self.volumes}")
        if not self.socket_dir.exists():
            logger.error(f"Host directory {self.socket_dir} does not exist!")
            self.socket_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
            
        if self.registry_proxy:
            self.registry_proxy.ensure_started()

            # Set proxy environment variables
            proxy_ip = self.registry_proxy.get_ip()
            self.environment.update({
                "HTTP_PROXY": f"http://{proxy_ip}:3128",
                "HTTPS_PROXY": f"http://{proxy_ip}:3128",
                "NO_PROXY": "localhost,127.0.0.1"
            })

        super().ensure_started()  # Use base class implementation

        if self.registry_proxy:
            # Inject the CA certificate into the container
            try:
                cacert = self.registry_proxy.get_cacert()
                self.inject_file(
                    content=cacert,
                    container_path="/usr/local/share/ca-certificates/registry-proxy-ca.crt",
                    mode=0o644
                )
                # Update CA certificates
                self.container.exec_run("update-ca-certificates")
            except Exception as e:
                logger.error(f"Failed to inject CA certificate: {e}")




        # Additional DinD-specific readiness check
        logger.debug("Checking Docker daemon readiness...")
        for attempt in range(self.ready_timeout):
            try:
                # Set ownership and permissions of socket file inside container
                self.container.exec_run(f"chown :{CURRENT_PRIMARY_GROUP} /dind-sockets/spirisdk_{self.container_name}.socket")
                self.container.exec_run(f"chmod 666 /dind-sockets/spirisdk_{self.container_name}.socket")
                
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
        return docker.DockerClient(base_url=f"unix:///tmp/dind-sockets/spirisdk_{self.container_name}.socket")
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

    async def run_compose(self, compose_file: str, max_attempts: int = 3):
        """Run docker compose with retry logic for network issues.
        
        Args:
            compose_file: Path to docker-compose.yaml file
            max_attempts: Maximum number of retry attempts (default: 3)

        Yields:
            str: Lines of output from the compose process

        Yields:
            str: Lines of output from the compose process

        Raises:
            RuntimeError: If compose fails after all retry attempts
        """
        logger.info(f"Running compose file: {compose_file}")
        
        paths = self._prepare_service_paths(compose_file)
        docker_host = f"unix://{self.socket_dir}/spirisdk_{self.container_name}.socket"
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
                proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "compose",
                    "--file", paths["compose_file"],
                    "--project-directory", paths["project_dir"],
                    "up",
                    "--detach",
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                # Stream stdout and stderr
                while True:
                    stdout_line = await proc.stdout.readline()
                    stderr_line = await proc.stderr.readline()
                    
                    if not stdout_line and not stderr_line:
                        break
                        
                    if stdout_line:
                        line = stdout_line.decode().strip()
                        if line:
                            yield f"stdout: {line}"
                    if stderr_line:
                        line = stderr_line.decode().strip()
                        if line:
                            yield f"stderr: {line}"

                # Check return code
                return_code = await proc.wait()
                if return_code == 0:
                    return
                else:
                    raise subprocess.CalledProcessError(return_code, proc.args)

            except subprocess.CalledProcessError as e:
                last_exception = e
                logger.warning(f"Compose attempt {attempt} failed: {str(e)}")
                if attempt < max_attempts:
                    await asyncio.sleep(5)  # Wait before retry

        raise RuntimeError(
            f"Failed to run compose after {max_attempts} attempts. Last error: {str(last_exception)}"
        )
