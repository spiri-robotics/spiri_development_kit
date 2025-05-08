import pytest
import requests
import time
import os
import tempfile
from pathlib import Path
from spiriSdk.dindocker import DockerInDocker

import tempfile

@pytest.fixture
def dind():
    """Fixture that provides a DockerInDocker instance and cleans up after."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set SDK_ROOT to our temp directory
        os.environ['SDK_ROOT'] = temp_dir
        with DockerInDocker(container_name="pytest_dind") as dind:
            yield dind
        # Clean up environment
        os.environ.pop('SDK_ROOT', None)

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
    compose_path = "robots/webapp-example/services/whoami/docker-compose.yaml"
    dind.run_compose(compose_path)

    # Verify directory was created
    test_dir = Path("./robot_data/pytest_dind/whoami/test")
    assert test_dir.exists(), "Compose should create expected directory"

    # Verify container is running
    client = dind.get_client()
    containers = client.containers.list()
    assert any('whoami-whoami-1' in c.name for c in containers), "whoami container should be running"

def test_web_service(dind):
    """Test the web service exposed by the compose file."""
    compose_path = "robots/webapp-example/services/whoami/docker-compose.yaml"
    dind.run_compose(compose_path)
    
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
