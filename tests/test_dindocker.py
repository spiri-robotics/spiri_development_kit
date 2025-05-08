import pytest
import requests
import time
from pathlib import Path
from spiriSdk.dindocker import DockerInDocker

@pytest.fixture
def dind():
    """Fixture that provides a DockerInDocker instance and cleans up after."""
    with DockerInDocker(container_name="pytest_dind") as dind:
        yield dind

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

    # Check if port 80 is listening
    response = requests.get(f"http://{dind.container_ip()}", timeout=5)
    assert response.status_code == 200, "Web service should respond with 200 OK"
    assert "whoami" in response.text, "Response should contain service name"
