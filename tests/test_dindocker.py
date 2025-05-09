import pytest
import requests
import time
import os
import tempfile
import shutil
import docker
from pathlib import Path
from spiriSdk.dindocker import DockerInDocker

def get_dind_containers(name_prefix="dind_"):
    """Helper to find any leftover dind containers from previous runs"""
    client = docker.from_env()
    return [c for c in client.containers.list(all=True) 
            if c.name.startswith(name_prefix)]

@pytest.fixture
def dind():
    """Fixture that provides a DockerInDocker instance and cleans up after."""
    # Create temp dir with relaxed permissions
    temp_dir = tempfile.mkdtemp()
    os.chmod(temp_dir, 0o777)  # Make writable by all
    
    try:
        # Set SDK_ROOT to our temp directory
        os.environ['SDK_ROOT'] = temp_dir
        with DockerInDocker() as dind:
            # Create shared compose file for all tests
            compose_content = """
version: '3'
services:
  whoami:
    image: traefik/whoami
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
            
            yield dind
    finally:
        # Clean up environment and temp dir
        os.environ.pop('SDK_ROOT', None)
        try:
            shutil.rmtree(temp_dir)
        except (OSError, shutil.Error) as e:
            print(f"Warning: Failed to clean up temp dir {temp_dir}: {e}")

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
    compose_path = Path(os.environ['SDK_ROOT']) / "whoami/docker-compose.yaml"
    dind.run_compose(str(compose_path))

    # Verify directory was created in the temp location
    test_dir = Path(os.environ['SDK_ROOT']) / "robot_data/pytest_dind/whoami/test"
    assert test_dir.exists(), f"Compose should create expected directory at {test_dir}"

    # Verify container is running
    client = dind.get_client()
    containers = client.containers.list()
    assert any('whoami-whoami-1' in c.name for c in containers), "whoami container should be running"

def test_web_service(dind):
    """Test the web service exposed by the compose file."""
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
