import asyncio
import subprocess
from pathlib import Path
import os

robot_paths = {
    'spiri-mu': '/robots/spiri-mu/models/spiri_mu/model.sdf'
}
class Robot:
    def __init__(self, name: str, type: str ='spiri-mu', number: float =1.0, position: list =[0, 0, 0.2, 0, 0, 0]):
        self.number = number
        self.name = name
        self.position = position
        self.position[0] = number
        self.path = robot_paths.get(type)

    def __str__(self):
        return f"Robot(name={self.name}, image={self.image}, options={self.options})"
    
    async def launch_robot(self, world_spawn: str = None) -> None:
        """Launch the robot in the Gazebo simulator."""
        pose = self.position
        ROS2_CMD = f"ros2 run ros_gz_sim create -world {world_spawn} -file {self.path} -name {self.name + str(self.number)} -x {pose[0]} -y {pose[1]} -z {pose[2]}"
        ros2_gz_create_proc = subprocess.Popen(
            ROS2_CMD.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )