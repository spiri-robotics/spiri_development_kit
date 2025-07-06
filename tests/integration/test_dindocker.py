"""
Integration tests for Docker-in-Docker container management.
These tests require Docker to be installed and running.
"""
import pytest
import time
from pathlib import Path
from spiriSdk.docker.dindocker import Container, DockerInDocker

@pytest.fixture
def temp_container():
    """Fixture that provides a clean test container"""
    container = Container(
        image_name="alpine:latest",
        container_name="test_container",
        command="tail -f /dev/null",  # Keep container running
        auto_remove=False
    )
    container.ensure_started()
    yield container
    container.cleanup()

@pytest.fixture
def temp_dind():
    """Fixture that provides a clean DockerInDocker container"""
    dind = DockerInDocker(
        container_name="test_dind",
        auto_remove=False
    )
    dind.ensure_started()
    yield dind
    dind.cleanup()

class TestContainer:
    def test_container_lifecycle(self, temp_container):
        """Test basic container start/stop operations"""
        assert temp_container.container.status == "running"
        
        temp_container.cleanup()
        with pytest.raises(RuntimeError):
            temp_container.get_ip()

    def test_file_injection(self, temp_container):
        """Test injecting a file into the container"""
        test_content = "test file content"
        test_path = "/tmp/test_file.txt"
        
        temp_container.inject_file(test_content, test_path)
        
        # Verify file exists with correct content
        exit_code, output = temp_container.container.exec_run(f"cat {test_path}")
        assert exit_code == 0
        assert output.decode().strip() == test_content

    def test_environment_variables(self):
        """Test container environment variable handling"""
        container = Container(
            image_name="alpine:latest",
            container_name="test_env_container",
            environment={"TEST_VAR": "test_value"},
            command="env",
            auto_remove=True
        )
        
        container.ensure_started()
        time.sleep(1)  # Give container time to run
        logs = container.container.logs().decode()
        assert "TEST_VAR=test_value" in logs

class TestDockerInDocker:
    def test_dind_lifecycle(self, temp_dind):
        """Test basic DinD container operations"""
        assert temp_dind.container.status == "running"
        
        # Verify Docker daemon is responsive
        client = temp_dind.get_client()
        assert client.ping()
        
        # Test running a container inside DinD
        test_container = client.containers.run(
            "alpine:latest",
            "echo hello world",
            remove=True
        )
        logs = test_container.logs().decode()
        assert "hello world" in logs

    def test_compose_operations(self, temp_dind):
        """Test docker compose operations through DinD"""
        # This would need a sample compose.yaml file in tests/fixtures
        pass  # Implement compose test once we have fixture files

    def test_volume_mounts(self, temp_dind):
        """Test volume mounting functionality"""
        test_file = Path("/tmp/test_volume_file.txt")
        test_file.write_text("volume test content")
        
        dind = DockerInDocker(
            container_name="test_volume_dind",
            volumes={str(test_file): {"bind": "/mnt/test_file.txt", "mode": "ro"}},
            auto_remove=False
        )
        dind.ensure_started()
        
        # Verify file was mounted correctly
        exit_code, output = dind.container.exec_run("cat /mnt/test_file.txt")
        assert exit_code == 0
        assert output.decode().strip() == "volume test content"
        
        dind.cleanup()
        test_file.unlink()
