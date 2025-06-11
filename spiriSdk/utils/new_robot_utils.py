import os, yaml, re, uuid, shutil, asyncio
from nicegui import ui, run
from pathlib import Path
from spiriSdk.docker.dindocker import DockerInDocker
from spiriSdk.utils.daemon_utils import daemons, start_services, DaemonEvent, active_sys_ids

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ROBOTS_DIR = os.path.join(ROOT_DIR, 'robots')

# Get the list of robots dynamically from the robots folder
robots = [folder for folder in os.listdir(ROBOTS_DIR) if os.path.isdir(os.path.join(ROBOTS_DIR, folder))]

class inputChecker:
    def __init__(self):
        self.inputs = {}
        self.isValid = False

    def addValid(self, i):
        self.inputs[i] = True
        self.update()

    def addNotValid(self, i):
        self.inputs[i] = False
        self.update()

    def reset(self):
        while len(self.inputs) > 1:
            self.inputs.popitem()
            self.update()

    def update(self):
        for v in self.inputs.values():
            if v is False:
                self.isValid = False
                return
        
        self.isValid = True

    def checkSelect(self, i: ui.select):
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()
    
    def checkText(self, i: ui.input):
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()

    def checkNumber(self, i: ui.number|None, ogValue: int|float = 0):
        self.inputs[i] = False
        if i.value:
            if 'Port' in i.label:
                if i.value >= 1000:
                    self.inputs[i] = True
            elif 'System ID' in i.label:
                if i.value not in active_sys_ids:
                    self.inputs[i] = True
                elif ogValue:
                    if float(i.value) == float(ogValue):
                        self.inputs[i] = True
            else:
                self.inputs[i] = True
        self.update()

    def checkForChanges(self, ogSettings, newSettings):
        self.update()
        if self.isValid == True:
            for key in newSettings:
                if newSettings[key] != ogSettings[key]:
                    return
            self.isValid = False
            return

def ensure_options_yaml():
    robots = []
    for folder in os.listdir(ROBOTS_DIR):
        folder_path = os.path.join(ROBOTS_DIR, folder)
        if os.path.isdir(folder_path):
            robots.append(folder)  # Add to the robots list
            options_path = os.path.join(folder_path, 'options.yaml')
            if not os.path.exists(options_path):
                # Create a default options.yaml file
                services_path = Path(folder_path) / "services"
                if not services_path.exists():
                    ui.notify(f"Services folder not found under {folder_path}", type="error")
                    continue
                service_folders = [p for p in services_path.iterdir() if p.is_dir()]
                if not service_folders:
                    ui.notify(f"No service folder found under {services_path}", type="error")
                    continue

                compose_file = service_folders[0] / "docker-compose.yaml"
                if not compose_file.exists():
                    compose_file = service_folders[0] / "docker-compose.yml"
                    if not compose_file.exists():
                        ui.notify(f"{compose_file} not found!", type="error")
                        continue
        
                compose_text = compose_file.read_text()
                variables = set(re.findall(r'\$[{]?([A-Z_][A-Z0-9_]*)[}]?', compose_text))

                default_options = {
                    'x-spiri-options': {}}
                for var in variables:
                    print(f"Detected variable: {var}")
                    if var not in default_options["x-spiri-options"]:
                        default_options["x-spiri-options"][var] = {
                            "type": "text",  # Default type (can be adjusted if needed)
                            "value": 0,  # Default to spiri.env value if available
                            "help-text": f"Auto-detected variable {var}"
                        }

                with open(options_path, 'w') as yaml_file:
                    yaml.dump(default_options, yaml_file)

    return robots

async def save_robot_config(robot_type, selected_options):
    if robot_type == "ARC":
        robot_id = selected_options.get('ARC_SYS_ID', uuid.uuid4().hex[:6])
    elif robot_type == "car":
        robot_id = selected_options.get('CAR_SYS_ID', uuid.uuid4().hex[:6])
    else:   
        robot_id = selected_options.get('DRONE_SYS_ID', uuid.uuid4().hex[:6])
    folder_name = f"{robot_type}-{robot_id}"
    folder_path = os.path.join(ROOT_DIR, "data", folder_name)

    os.makedirs(folder_path, exist_ok=True)

    config_path = os.path.join(folder_path, "config.env")
    with open(config_path, "w") as f:
        for key, value in selected_options.items():
            f.write(f"{key}={value}\n")

    new_daemon = DockerInDocker(image_name="docker:dind", container_name=folder_name)
    await run.io_bound(new_daemon.ensure_started)
    daemons[folder_name] = new_daemon
    active_sys_ids.append(robot_id)

    await start_services(folder_name)
    await DaemonEvent.notify()

    # ui.notify(f"Saved config.env and started daemon for {folder_name}")
    ui.notify(f"Robot {folder_name} added successfully!")

async def delete_robot(robot_name) -> bool:
    robot_path = os.path.join(ROOT_DIR, "data", robot_name)
    daemon = daemons.pop(robot_name)
    daemon.cleanup()
    robot_sys = str(robot_name).rsplit('-', 1)
    active_sys_ids.remove(int(robot_sys[1]))
    if os.path.exists(robot_path):
        shutil.rmtree(robot_path)
    await DaemonEvent.notify()
    return True

def display_robot_options(robot_name, selected_additions, selected_options, options_container, checker: inputChecker):
    options_path = os.path.join(ROBOTS_DIR, robot_name, 'options.yaml')
    if not os.path.exists(options_path):
        ui.notify(f"No options.yaml found for {robot_name}")
        options_container.clear()
        with options_container:
            ui.label(f'No options.yaml found for {robot_name}')
        return

    with open(options_path, 'r') as yaml_file:
        options = yaml.safe_load(yaml_file)

    selected_options.clear()
    for key, option in options.get('x-spiri-options', {}).items():
        selected_options[key] = option.get('value')

    format_rules = {
        'Arc': 'ARC',
        'Sys': 'System',
        'Id': 'ID',
        'Mavros': 'MAVROS',
        'Gcs': 'GCS',
        'Serial0': 'Serial',
        'Sitl': 'SITL'
    }

    # Clear previous options UI
    options_container.clear()

    # Display options dynamically
    with options_container:
        for key, option in options.get('x-spiri-options', {}).items():
            help_text = option.get('help-text', False)
            option_type = option.get('type', 'text')
            current_value = option.get('value', '')

            formatted_key = str(key).replace("_", " ").title()
            for og, new in format_rules.items():
                formatted_key = formatted_key.replace(og, new)

            if option_type == 'bool':
                if current_value == 1:
                    bool_value = True
                else:
                    bool_value = False

                def on_toggle(e, k):
                    if e.value == True:
                        selected_options[k] = 1
                    else:
                        selected_options[k] = 0
                
                with ui.row().classes('items-center justify-between w-[35%]'):
                    ui.label(formatted_key)
                    ui.switch(value=bool_value, on_change=lambda e, k=key: on_toggle(e, k))

            elif option_type == 'int' or option_type == 'float':
                min_val = option.get('min', None)
                max_val = option.get('max', None)
                step = option.get('step', 1)
                current_value = option.get('value', 0)

                def handleNum(e, k):
                    checker.checkNumber(e)

                    if e.value is not None:
                        if e.value == int(e.value):
                            selected_options[k] = int(e.value)
                        else:
                            selected_options[k] = e.value

                if 'SYS_ID' in key:
                    numVal = None
                else:
                    numVal = current_value

                numInput = ui.number(
                    label=f'{formatted_key}*',
                    value=numVal,
                    min=min_val,
                    max=max_val,
                    step=step,
                    on_change=lambda e, k=key: handleNum(e.sender, k),
                    validation={
                        'Field cannot be empty or contain letters': lambda value: value,
                        'Value must be four or more digits': lambda value, label=formatted_key: value >= 1000 if 'Port' in label else True,
                        'System ID already in use': lambda value, label=formatted_key: value not in active_sys_ids if 'System ID' in label else True
                    }
                ).classes('w-full pb-1')
                
                if 'SYS_ID' in key:
                    numInput.props('hint="System ID cannot be changed once set"')
                    numInput.classes('pb-4')
                    checker.addNotValid(numInput)
                else:
                    checker.addValid(numInput)
            
            elif option_type == 'dropdown':
                def handleDropdown(e, k):
                    selected_options[k] = e.value
                    checker.checkSelect(e)

                # Ensure the dropdown options are a list
                dropdown_options = option.get('options', [])
                if isinstance(dropdown_options, list):
                    drop = ui.select(
                        options=dropdown_options, 
                        label=formatted_key,
                        value=current_value,
                        on_change=lambda e, k=key: handleDropdown(e.sender, k),
                    ).classes('w-full')
                    if drop.value is not None:
                        checker.addValid(drop)
                    else:
                        checker.addNotValid(drop)
                else:
                    ui.label(f"Invalid dropdown options for {key}").classes('text-body2')
            
            else:
                def handleText(e: ui.input, k):
                    selected_options.update({k: e.value})
                    checker.checkText(e)

                if 'NAME' in key:
                    textVal = ''
                else:
                    textVal = current_value
                    
                textInput = ui.input(
                    label=f'{formatted_key}*', 
                    value=textVal, 
                    placeholder=current_value, 
                    on_change=lambda e, k=key: handleText(e.sender, k),
                    validation={
                        'Field cannot be empty': lambda value: len(value) > 0
                    }
                ).classes('w-full pb-1')

                if 'NAME' in key:
                    checker.addNotValid(textInput)
                else:
                    checker.addValid(textInput)