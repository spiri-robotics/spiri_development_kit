import pytest
import requests
import time
import os
import tempfile
import shutil
import docker
from pathlib import Path
from loguru import logger
from spiriSdk.docker.dindocker import DockerInDocker, DockerRegistryProxy
from spiriSdk.docker.dindocker import DockerInDocker, DockerRegistryProxy

def get_dind_containers(name_prefix="dind_"):
    """Helper to find any leftover dind containers from previous runs"""
    client = docker.from_env()
    return [c for c in client.containers.list(all=True) 
            if c.name.startswith(name_prefix)]

@pytest.fixture(scope="module")
def registry_proxy():
    """Fixture that provides a registry proxy instance."""
    proxy = DockerRegistryProxy()
    yield proxy
    proxy.cleanup()

@pytest.fixture
def dind(registry_proxy):
    """Fixture that provides a DockerInDocker instance and cleans up after."""
    # Create temp dir with relaxed permissions
    old_umask = os.umask(0)
    try:
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0o777)  # Make writable by all
    finally:
        os.umask(old_umask)
    
    try:
        # Set SDK_ROOT to our temp directory
        os.environ['SDK_ROOT'] = temp_dir
        with DockerInDocker(registry_proxy=registry_proxy) as dind:
            # Create shared compose file for all tests
            compose_content = """
services:
  whoami:
    image: traefik/whoami:v1.10.1  # Use specific version tag
    ports:
      - "80:80"
    volumes:
      - ./test:/test
"""
            whoami_dir = Path(temp_dir) / "whoami"
            whoami_dir.mkdir(parents=True, exist_ok=True)
            compose_path = whoami_dir / "docker-compose.yaml"
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            # Try to pre-pull the test image to avoid timeouts during test
            try:
                client = dind.get_client()
                client.images.pull("traefik/whoami:v1.10.1")
                logger.success("Successfully pre-pulled test image")
            except Exception as e:
                logger.warning(f"Could not pre-pull test image: {e}")
            
            yield dind
    finally:
        # Clean up environment and temp dir
        os.environ.pop('SDK_ROOT', None)
        try:
            # Try normal removal - if this fails due to permissions, we can ignore it
            # since it's just test temp data and will be cleaned up by system eventually
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Could not clean up temp dir {temp_dir} - this is non-critical and can be ignored")

def test_dind_startup(dind):
    """Test basic Docker-in-Docker container startup."""
    # Verify we got an IP
    ip = dind.container_ip()
    assert ip, "Container should have an IP address"

    # Verify Docker connection
    client = dind.get_client()
    version = client.version()
    assert version['Version'], "Should get Docker version info"

def test_compose_operations(dind):
    """Test running docker-compose operations."""
    # First verify we can resolve Docker Hub
    import socket
    try:
        socket.gethostbyname('registry-1.docker.io')
    except socket.gaierror as e:
        pytest.fail(f"Cannot resolve registry-1.docker.io: {str(e)}")

    compose_path = Path(os.environ['SDK_ROOT']) / "whoami/docker-compose.yaml"
    dind.run_compose(str(compose_path))

    # Verify directory was created in the temp location
    test_dir = Path(os.environ['SDK_ROOT']) / f"data/{dind.container_name}/whoami/test"
    # Wait up to 5 seconds for directory to appear
    for _ in range(5):
        if test_dir.exists():
            break
        time.sleep(1)
    assert test_dir.exists(), f"Compose should create expected directory at {test_dir}"

    # Verify container is running (with retry)
    client = dind.get_client()
    for _ in range(10):  # Wait up to 10 seconds
        containers = client.containers.list()
        if any('whoami-whoami-1' in c.name for c in containers):
            break
        time.sleep(1)
    else:
        assert False, "whoami container should be running"

def test_registry_proxy_connectivity(dind):
    """Test basic network connectivity between DinD and registry proxy."""
    
    # Verify registry proxy is running
    assert dind.registry_proxy is not None
    assert dind.registry_proxy.container is not None
    assert dind.registry_proxy.container.status == "running"
    
    # Get proxy IP
    proxy_ip = dind.registry_proxy.container_ip()
    
    # Verify proxy can resolve Docker Hub
    try:
        output = dind.registry_proxy.container.exec_run("nslookup registry-1.docker.io")
        assert output.exit_code == 0, f"DNS lookup failed with exit code {output.exit_code}"
        output_text = output.output.decode()
        assert "Address:" in output_text, f"Expected DNS resolution output, got: {output_text}"
    except docker.errors.APIError as e:
        pytest.fail(f"Failed to resolve registry-1.docker.io from proxy: {str(e)}")
    
    # Simple ping test from DinD to proxy
    try:
        output = dind.container.exec_run(f"ping -c 1 {proxy_ip}")
        assert output.exit_code == 0, f"Ping failed with exit code {output.exit_code}"
        output_text = output.output.decode()
        assert ("1 packets transmitted, 1 received" in output_text or 
                "1 packets transmitted, 1 packets received" in output_text), \
               f"Expected ping success output, got: {output_text}"
    except docker.errors.APIError as e:
        pytest.fail(f"Failed to ping registry proxy: {str(e)}")

def test_cacert_injection(dind):
    """Test that the registry proxy CA cert was properly injected into DinD."""
    
    # Verify registry proxy is running
    assert dind.registry_proxy is not None
    
    # Get the expected CA cert from the proxy
    expected_cert = dind.registry_proxy.get_cacert()
    
    # Check the cert exists in the DinD container
    result = dind.container.exec_run("cat /usr/local/share/ca-certificates/registry-ca.crt")
    assert result.exit_code == 0, "Failed to read CA cert from DinD container"
    injected_cert = result.output.decode().strip()
    
    # Verify cert contents match
    assert injected_cert == expected_cert, "CA cert in DinD container doesn't match proxy cert"

def test_web_service(dind):
    """Test the web service exposed by the compose file."""
    # First verify we can resolve Docker Hub
    import socket
    try:
        socket.gethostbyname('registry-1.docker.io')
    except socket.gaierror as e:
        pytest.fail(f"Cannot resolve registry-1.docker.io: {str(e)}")

    # First verify we can resolve Docker Hub
    import socket
    try:
        socket.gethostbyname('registry-1.docker.io')
    except socket.gaierror as e:
        pytest.fail(f"Cannot resolve registry-1.docker.io: {str(e)}")

    compose_path = Path(os.environ['SDK_ROOT']) / "whoami/docker-compose.yaml"
    dind.run_compose(str(compose_path))
    
    # Wait for service to be ready (max 30 seconds)
    max_attempts = 30
    last_exception = None
    ip = dind.container_ip()
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://{ip}", timeout=1)
            if response.status_code == 200:
                assert "Hostname:" in response.text, "Response should contain host information"
                return  # Success!
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            last_exception = e
            time.sleep(1)
    
    # If we get here, all attempts failed
    pytest.fail(f"Service not ready after {max_attempts} attempts. Last error: {str(last_exception)}")

def test_registry_proxy_certificate():
    """Test that the registry proxy generates a valid certificate."""
    with DockerRegistryProxy() as registry_proxy:
        # Get the certificate from fullchain.pem
        cert = registry_proxy.get_cacert()
        logger.info(f"Got certificate: {cert[:100]}...")  # Print first 100 chars
        
        # Basic validation of the certificate
        assert cert.startswith("-----BEGIN CERTIFICATE-----"), "Certificate should start with PEM header"
        assert "-----END CERTIFICATE-----" in cert, "Certificate should end with PEM footer"
        assert len(cert) > 100, "Certificate should be more than just headers"
        
        # Verify the certificate is stable across multiple calls
        cert2 = registry_proxy.get_cacert()
        assert cert == cert2, "Certificate should be stable across multiple calls"

def test_socket_creation(dind):
    """Test that the Docker socket is created in the specified directory."""
    # Get the socket path from the container's command
    socket_name = f"{dind.container_name}.socket"
    socket_path = dind.socket_dir / socket_name
    
    # Verify socket exists on host
    assert socket_path.exists(), f"Socket file {socket_path} should exist on host"
    assert socket_path.is_socket(), f"{socket_path} should be a socket file"
    
    # Verify socket exists in container
    result = dind.container.exec_run(f"ls -la /dind-sockets/{socket_name}")
    assert result.exit_code == 0, f"Failed to list socket in container: {result.output.decode()}"
    
    # Verify socket permissions (should be 666)
    host_perms = oct(socket_path.stat().st_mode)[-3:]
    assert host_perms == '666', f"Socket should have 666 permissions, got {host_perms}"
