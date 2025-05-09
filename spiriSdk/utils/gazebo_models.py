import asyncio
import subprocess
from pathlib import Path
import os

class Robot:
    def __init__(self, name, position=[0, 0, 0, 0, 0, 0]):
        self.name = name
        self.position = position

    def __str__(self):
        return f"Robot(name={self.name}, image={self.image}, options={self.options})"
    
    async def launch_robot(self, world):
        ROS2_CMD = f"ros2 run ros_gz_sim create -world {world} -file /robots/spiri-mu/models/spiri_mu/model.sdf -name {self.name} -x 0 -y 0 -z 0"
        ros2_gz_create_proc = subprocess.Popen(
            ROS2_CMD.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
