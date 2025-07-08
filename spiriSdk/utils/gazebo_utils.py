import subprocess, time

from pathlib import Path
from loguru import logger
from typing import Optional

from spiriSdk.utils.daemon_utils import daemons

MODEL_PATHS = {
    'spiri_mu': 'robots/spiri_mu/models/spiri_mu',
    'spiri_mu_no_gimbal': 'robots/spiri_mu_no_gimbal/models/spiri_mu',
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

def get_running_worlds() -> list:
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
                            world_name = Path(token).stem
                            running_worlds.append(world_name)
            return running_worlds
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command: {e}")

class World:
    def __init__(self, name):
        self.name = name
        self.models: dict[str:Model]  = {}

    def get_name(self) -> str:
        return self.name
    
    async def prep_bot(self, model_name: str ='bot', model_type: str='spiri_mu_no_gimbal', ip: str='127.0.0.1'):
        
        model = Model(self, model_name, model_type, ip, daemon=daemons[model_name])
        await model.launch_model()
        self.models.update({model_name:model})
        return

    async def run_world(self) -> None:
        """Run world in Gazebo simulator."""
        try:
            cmd = ['gz', 'sim', '-r', f'{WORLD_PATHS[self.name]}.world']
            subprocess.Popen(cmd)
            logger.success('world started')
        except FileNotFoundError:
            logger.error(f"File not found: {self.name}. Make sure it is installed and available in the PATH.")

    async def reset(self, name):
        running_world = get_running_worlds()
        if len(running_world) > 0:
            self.end_gz_proc()
        self.name = name
        self.models = {
        
        }
        time.sleep(1)
        await self.run_world()
    
    def end_gz_proc(self) -> None:
        try:
            KILL_GZ_CMD = f"pkill -f 'gz sim -r {WORLD_PATHS[self.name]}.world'"
            dead_world_models = {} 
            dead_world_models.update(self.models)
            for model in dead_world_models.values(): 
                model.kill_model()
            self.models = {}
            remove_gazebo_proc = subprocess.Popen(
                KILL_GZ_CMD, 
                shell=True, 
                stdout=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command: {e}")

class Model:
    def __init__(self, parent: World, name: str, type: str ='spiri_mu', ip: str = '127.0.0.1', position: Optional[list[int]] = None, daemon=None ):
        self.parent: World = parent
        self.name = name
        self.type = type
        self.path = MODEL_PATHS.get(type)
        self.position = position
        self.daemon = daemon
        self.sys_id = int(self.daemon.env_get('MAVLINK_SYS_ID', 0))
        self.sitl_port = 9002 + 10 * self.sys_id
        logger.debug(f"Model {self.name} of type {self.type} will use SITL port {self.sitl_port}")

        if self.position == None:
            self.position = [self.sys_id, 0, 0, 0, 0, 0]
        if type == 'spiri_mu' or type == 'spiri_mu_no_gimbal':
            self.position[2] = self.position[2] + 0.3


    async def launch_model(self) -> bool:
        """Launch the model in the Gazebo simulator."""
        logger.debug("adding model")
        if (self.type == 'spiri_mu' or self.type == 'spiri_mu_no_gimbal'):
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

running_world = get_running_worlds()
if len(running_world) > 0:
    gz_world = World(running_world[0])
else:
    gz_world = World('empty_world')