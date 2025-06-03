from pathlib import Path
import subprocess
import os
robot_paths = {
    'spiri_mu': '/robots/spiri_mu/models/spiri_mu/model.sdf',
    'spiri_mu_no_gimbal': '/robots/spiri_mu_no_gimbal/models/spiri_mu/model.sdf',
    'dummy_test': '/robots/dummy_test/models/car_008/model.sdf',
    'ARC': '/robots/ARC/models/ARC_simplified/model.sdf'
}

class Gazebo:
    def __init__(self):
        self.worlds = {}
        self.running_worlds = ['empty_world']
        self.running_robots = []
        self.find_worlds()

    def find_worlds(self, p: Path = Path('./worlds')) -> dict:
        """Find all worlds in the given directory."""
        self.worlds = {'empty_world': World(self, 'empty_world')}
        try:
            for subdir in p.iterdir():
                if subdir.is_dir():
                    for world in subdir.rglob('*.world'):
                        world = World(self, subdir.name)
                        self.worlds.update({subdir.name: None})
                        print(subdir.name)
        except FileNotFoundError:
            print(f"Directory not found: {p}. Make sure it exists.")
        
    async def get_running_worlds(self) -> list:
        """Get a list of running Gazebo world names."""
        try:
            cmd = "ps aux | grep '[g]z sim'"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            output = output.decode('utf-8')
            self.running_worlds.clear()
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    command = ' '.join(parts[10:])  # Command starts around field 11
                    for token in command.split():
                        if token.endswith('.world'):
                            world_file = os.path.basename(token)
                            world_name = os.path.splitext(world_file)[0]
                            self.running_worlds.append(world_name)

            for name in self.worlds.keys():
                if name not in self.running_worlds:
                    self.worlds[name] = None

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
    
    async def start_world(self, name, run_value):
        world = World(self, name)
        await self.kill_all_worlds()
        await world.run_world(run_value)
        self.worlds[name] = world
        print(f'start:{world.name}')

    async def kill_all_worlds(self):
        try:
            cmd = "pkill -f 'gz sim'"
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            print(f"closed: {self.running_worlds}")
            await self.get_running_worlds()
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

class World:
    def __init__(self, parent, name: str):
        self.parent: Gazebo = parent
        self.name = name
        self.running = False
        self.robots = {

        }

    def get_name(self) -> str:
        return self.name
    
    async def prep_bot(self, robot_name: str ='bot', robot_type: str='spiri_mu_no_gimbal'):
        bot = Robot(self, robot_name, robot_type)
        await bot.launch_robot()
        self.robots.update({robot_name:bot})

    async def run_world(self, auto_run: str = '') -> None:
        """Run world in Gazebo simulator."""
        print(f"Running world: {self.name}")
        try:
            if auto_run == 'Running':
                cmd = ['gz', 'sim', '-r', f'./worlds/{self.name}/worlds/{self.name}.world']
            else:
                cmd = ['gz', 'sim', f'./worlds/{self.name}/worlds/{self.name}.world']
            subprocess.Popen(cmd)
        
        except FileNotFoundError:
            print(f"File not found: {self.name}. Make sure it is installed and available in the PATH.")

class Robot:
    def __init__(self, parent: World, name: str, type: str ='spiri-mu', position: list[int] = None):
        self.parent: World = parent
        self.name = name
        self.path = robot_paths.get(type)
        self.position = position

        if self.position == None:
            self.position = [len(self.parent.robots.keys()) + 1, 0, 0, 0, 0, 0]
            if type == 'spiri_mu' or type == 'spiri_mu_no_gimbal':
                self.position[2] = 0.2
        else:
            print("smthn wrong")
    
    async def launch_robot(self) -> None:
        """Launch the robot in the Gazebo simulator."""

        ROS2_CMD = f"ros2 run ros_gz_sim create -world {self.parent.name} -file {self.path} -name {self.name} -x {self.position[0]} -y {self.position[1]} -z {self.position[2]}"
        ros2_gz_create_proc = subprocess.Popen(
            ROS2_CMD.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

