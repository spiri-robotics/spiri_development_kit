from pathlib import Path
import subprocess
import os


async def find_worlds(p = Path('./worlds')):
    worlds = {'empty_world': 'empty.world'}
    try:
        for subdir in p.iterdir():
            if subdir.is_dir():
                for world in subdir.rglob('*.world'):
                    worlds.update({subdir.name:world.name})
        print(worlds)
        return worlds
    except FileNotFoundError:
        print(f"Directory not found: {p}. Make sure it exists.")
        return []
    
class World:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.running = False

    async def run_world(self, auto_run= ''):
        name = self.name
        dir = self.path
        try:
            if auto_run == 'Running':
                cmd = ['gz', 'sim', '-r', f'./worlds/{dir}/worlds/{name}']
            else:
                cmd = ['gz', 'sim', f'./worlds/{dir}/worlds/{name}']
            running_worlds = [dir, name]
            print(running_worlds)
            subprocess.Popen(cmd)
            return running_worlds
        
        except FileNotFoundError:
            print(f"File not found: {name}. Make sure it is installed and available in the PATH.")