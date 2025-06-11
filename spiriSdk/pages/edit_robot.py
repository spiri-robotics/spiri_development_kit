from nicegui import ui
import os, yaml
from spiriSdk.utils.new_robot_utils import inputChecker, save_robot_config, delete_robot
from spiriSdk.utils.daemon_utils import active_sys_ids

ogSettings = {}
newSettings = {}

@ui.refreshable
def display(robotID, checker: inputChecker):
    
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_folder_name = f"{robotID}"
    config_folder_path = os.path.join(ROOT_DIR, "data", config_folder_name)
    config_file_path = os.path.join(config_folder_path, "config.env")

    ogSettings.clear()
    newSettings.clear()

    with open(config_file_path, 'r') as current:
        for line in current:
            line = line.replace('\n', '')
            s = line.split('=')
            ogSettings[s[0]] = s[1]
            newSettings[s[0]] = s[1]

    # Add additional if-statements if any other robot types are added
    if 'spiri_mu' in robotID:
        if 'no_gimbal' in robotID:
            default_folder_name = robotID[:18]
        else:
            default_folder_name = robotID[:8]
    else:
        default_folder_name = robotID[:3]

    default_folder_path = os.path.join(ROOT_DIR, 'robots', default_folder_name)
    default_file_path = os.path.join(default_folder_path, 'options.yaml')

    format_rules = {
        'Arc': 'ARC',
        'Sys': 'System',
        'Id': 'ID',
        'Mavros': 'MAVROS',
        'Gcs': 'GCS',
        'Serial0': 'Serial',
        'Sitl': 'SITL'
    }

    for key, val in ogSettings.items():
        formatted_key = str(key).replace("_", " ").title()
        for og, new in format_rules.items():
            formatted_key = formatted_key.replace(og, new)

        with open(default_file_path, 'r') as d:
            default = yaml.safe_load(d)

        defSettingPath = default.get('x-spiri-options').get(key)
        settingType = defSettingPath.get('type')

        if settingType != 'bool':
            try:
                val = float(val)
                if val == int(val):
                    val = int(val)
            except:
                pass

        # display current settings dynamically
        if settingType == 'bool':
            if val == '1':
                bool_value = True
            else:
                bool_value = False

            def on_toggle(e, k):
                if e.value == True:
                    newSettings[k] = '1'
                else:
                    newSettings[k] = '0'

                checker.checkForChanges(ogSettings, newSettings)
            
            with ui.row().classes('items-center justify-between w-[35%]'):
                ui.label(f'{formatted_key}:')
                ui.switch(value=bool_value, on_change=lambda e, k=key: on_toggle(e.sender, k))

        elif settingType == 'int' or settingType == 'float':
            val = float(val)
            min_val = defSettingPath.get('min', None)
            max_val = defSettingPath.get('max', None)
            step = defSettingPath.get('step', None)
            
            def handleNum(e, k, ogValue):
                if e.value is not None:
                    n = e.value
                    if int(e.value) == e.value:
                        n = int(n)
                    newSettings[k] = str(n)

                checker.checkNumber(e, ogValue)
                checker.checkForChanges(ogSettings, newSettings)

            numInput = ui.number(
                formatted_key, 
                value=val, 
                min=min_val, 
                max=max_val, 
                step=step, 
                on_change=lambda e, k=key, ogValue=val: handleNum(e.sender, k, ogValue),
                validation={
                    'Field cannot be empty or contain letters': lambda value: value,
                    'Value must be four or more digits': lambda value, label=formatted_key: value >= 1000 if 'Port' in label else True
                }
            )

            if 'SYS_ID' in key:
                numInput.disable()
            else:
                checker.addValid(numInput)
        else:
            def handleText(e: ui.input, k):
                newSettings[k] = e.value
                checker.checkText(e)
                checker.checkForChanges(ogSettings, newSettings)

            textInput = ui.input(
                formatted_key, 
                value=val, 
                on_change=lambda e, k=key: handleText(e.sender, k),
                validation={
                    'Field cannot be empty': lambda value: len(value) > 0
                }
            ).classes('w-full')

            checker.addValid(textInput)

    checker.checkForChanges(ogSettings, newSettings)


@ui.page('/edit_robot')
async def edit_robot(robotID, checker):
    ui.label(f'Edit {robotID}').classes('text-h5')
    display(robotID, checker)

def save_changes(robotID):
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_folder_name = f"{robotID}"
    config_folder_path = os.path.join(ROOT_DIR, "data", config_folder_name)
    config_file_path = os.path.join(config_folder_path, "config.env")

    with open(config_file_path, 'w') as f:
        for key, val in newSettings.items():
            f.write(f'{key}={val}\n')

    ui.notify(f'{robotID} updated successfully!')

def clear_changes(robotID, checker):
    display.refresh(robotID, checker)