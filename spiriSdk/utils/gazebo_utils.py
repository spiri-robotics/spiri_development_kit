from pathlib import Path
from dataclasses import field
from spiriSdk.utils.daemon_utils import ROBOTS_DIR, ROOT_DIR, DATA_DIR
import subprocess
import os
import time

MODEL_PATHS = {
    'spiri_mu': 'robots/spiri_mu/models/spiri_mu',
    'spiri_mu_no_gimbal': 'robots/spiri_mu_no_gimbal/models/spiri_mu',
    'car': 'robots/car/models/car_008',
    'ARC': 'robots/ARC/models/ARC_simplified'
}

WORLD_PATHS = {
    'empty_world': 'worlds/empty_world/worlds/empty_world',
    'citadel_hill': 'worlds/citadel_hill/worlds/citadel_hill',
    'yarmouth_airport': 'worlds/yarmouth_airport/worlds/yarmouth_airport'
}
def is_robot_alive(name):
    if name in gz_world.models.keys():
        return True
    else:
        return False

async def get_running_worlds() -> list:
        """Get a list of running Gazebo world names."""
        try:
            running_worlds = []
            cmd = "ps aux | grep '[g]z sim'"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            output = output.decode('utf-8')
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    command = ' '.join(parts[10:])
                    for token in command.split():
                        if token.endswith('.world'):
                            world_file = os.path.basename(token)
                            world_name = os.path.splitext(world_file)[0]
                            running_worlds.append(world_name)
            return running_worlds
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

class World:
    def __init__(self, name):
        self.name = name
        self.models: dict[str:Model]  = {}
        self.run_value = ''

    def get_name(self) -> str:
        return self.name
    
    async def prep_bot(self, model_name: str ='bot', model_type: str='spiri_mu_no_gimbal', ip: str='127.0.0.1'):
        model = Model(self, model_name, model_type, ip)
        await model.launch_model()
        self.models.update({model_name:model})
        return

    async def run_world(self, run_value) -> None:
        """Run world in Gazebo simulator."""
        print(f"Running world: {self.name}")
        self.run_value = run_value
        try:
            if self.run_value == '-r ':
                cmd = ['gz', 'sim', '-r', f'{WORLD_PATHS[self.name]}.world']
            else:
                cmd = ['gz', 'sim', f'{WORLD_PATHS[self.name]}.world']
            subprocess.Popen(cmd)
            running_world = await get_running_worlds()
            print('world started')
        except FileNotFoundError:
            print(f"File not found: {self.name}. Make sure it is installed and available in the PATH.")

    async def reset(self, name, run_value):
        self.end_gz_proc()
        self.name = name
        self.models = {
        
        }
        time.sleep(1)
        await self.run_world(run_value)
    
    def end_gz_proc(self) -> None:
        try:
            KILL_GZ_CMD = f"pkill -f 'gz sim {self.run_value}{WORLD_PATHS[self.name]}.world'"
            print(KILL_GZ_CMD)
            dead_world_models = {} 
            dead_world_models.update(self.models)
            for model in dead_world_models.values(): 
                model.kill_model()
            models = {}
            remove_gazebo_proc = subprocess.Popen(
                KILL_GZ_CMD, 
                shell=True, 
                stdout=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

class Model:
    def __init__(self, parent: World, name: str, type: str ='spiri_mu', ip: str = '127.0.0.1', position: list[int] = None):
        self.parent: World = parent
        self.name = name
        self.type = type
        self.path = MODEL_PATHS.get(type)
        self.position = position
        self.sitl_port = '9002'
        self.ip = ip
        self.get_model_sitl_port()

        if self.position == None:
            self.position = [len(self.parent.models.keys()) + 1, 0, 0, 0, 0, 0]
        if type == 'spiri_mu' or type == 'spiri_mu_no_gimbal':
            self.position[2] = self.position[2] + 0.195

    def get_model_sitl_port(self) -> None:
        config_path = Path(f'/data/{self.name}/config.env')
        if config_path.exists():
            with open(config_path) as f:
                for line in f:
                    if line.startswith('SITL_PORT='):
                        self.sitl_port =line.strip().split('=', 1)[1]

    async def launch_model(self) -> bool:
        """Launch the model in the Gazebo simulator."""
        print("adding model")
        print(self.path)
        if (self.type == 'spiri_mu'):
            XACRO_CMD = [
                "xacro",
                f"fdm_port_in:={self.sitl_port}",
                "model.xacro.sdf",
                "-o",
                "model.sdf",
            ]
            xacro_proc = subprocess.Popen(
                XACRO_CMD,
                cwd=f"{self.path}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
        ROS2_CMD = f"ros2 run ros_gz_sim create -world {self.parent.name} -file {self.path}/model.sdf -name {self.name} -x {self.position[0]} -y {self.position[1]} -z {self.position[2]}"        
        ros2_gz_create_proc = subprocess.Popen(
            ROS2_CMD.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        out, err = ros2_gz_create_proc.communicate(timeout=3)
        ros2_gz_create_proc.kill()
        return True

    
    def kill_model(self):
        
        # http://osrf-distributions.s3.amazonaws.com/gazebo/api/7.1.0/classgazebo_1_1physics_1_1Entity.html
        ENTITY_TYPE_MODEL = 0x00000002
        REQUEST_ARG = f"name: '{self.name}' type: {ENTITY_TYPE_MODEL}"
        
        GZ_SERVICE_CMD = [
            "gz",
            "service",
            "-s",
            f"/world/{self.parent.name}/remove",
            "--reqtype",
            "gz.msgs.Entity",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "5000",
            "--req",
            REQUEST_ARG
        ]
        remove_entity_proc = subprocess.Popen(
            GZ_SERVICE_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        out, err = remove_entity_proc.communicate(timeout=3)
        remove_entity_proc.kill()
        del self.parent.models[self.name]

gz_world = World('empty_world')