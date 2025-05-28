import asyncio
import subprocess
from pathlib import Path
import os

robot_paths = {
    'spiri_mu': '/robots/spiri_mu/models/spiri_mu/model.sdf',
    'spiri_mu_no_gimbal': '/robots/spiri_mu_no_gimbal/models/spiri_mu/model.sdf',
    'dummy_test': '/robots/dummy_test/models/car_008/model.sdf'
}
class Robot:
    def __init__(self, name: str, type: str ='spiri-mu', position: list =[0, 0, 0.2, 0, 0, 0]):
        self.name = name
        self.position = position
        self.path = robot_paths.get(type)
        print(f"Robot path: {self.path}")

    def __str__(self):
        return f"Robot(name={self.name}, image={self.image}, options={self.options})"
    
    async def launch_robot(self, world_spawn: str = None) -> None:
        """Launch the robot in the Gazebo simulator."""
        pose = self.position
        ROS2_CMD = f"ros2 run ros_gz_sim create -world {world_spawn} -file {self.path} -name {self.name} -x {pose[0]} -y {pose[1]} -z {pose[2]}"
        ros2_gz_create_proc = subprocess.Popen(
            ROS2_CMD.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )