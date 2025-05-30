from pathlib import Path
import subprocess

async def find_worlds(p: Path = Path('./worlds')) -> dict:
    """Find all worlds in the given directory."""
    worlds = {'empty_world': World('empty_world.world', 'empty_world')}
    try:
        for subdir in p.iterdir():
            if subdir.is_dir():
                for world in subdir.rglob('*.world'):
                    world = World(world.name, subdir.name)
                    worlds.update({subdir.name: world})
        return worlds
    except FileNotFoundError:
        print(f"Directory not found: {p}. Make sure it exists.")
        return worlds
    
class World:
    def __init__(self, name: str , path: str):
        self.name = name
        self.path = path
        self.running = False

    def get_name(self) -> str:
        return self.name
    
    async def run_world(self, auto_run: str = '') -> list:
        """Run world in Gazebo simulator."""
        print(f"Running world: {self.name}")
        try:
            if auto_run == 'Running':
                cmd = ['gz', 'sim', '-r', f'./worlds/{self.path}/worlds/{self.name}']
            else:
                cmd = ['gz', 'sim', f'./worlds/{self.path}/worlds/{self.name}']
            running_worlds = [self.path, self.name]
            subprocess.Popen(cmd)
            return running_worlds
        
        except FileNotFoundError:
            print(f"File not found: {self.name}. Make sure it is installed and available in the PATH.")