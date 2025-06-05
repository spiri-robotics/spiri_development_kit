from nicegui import ui
import os, yaml

settings = {}

@ui.refreshable
def display(robotID):
    
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_folder_name = f"{robotID}"
    config_folder_path = os.path.join(ROOT_DIR, "data", config_folder_name)
    config_file_path = os.path.join(config_folder_path, "config.env")

    settings.clear()

    with open(config_file_path, 'r') as current:
        for line in current:
            line = line.replace('\n', '')
            s = line.split('=')
            settings[s[0]] = s[1]

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

    for key, val in settings.items():
        formatted_key = str(key).replace("_", " ").title()
        for og, new in format_rules.items():
            formatted_key = formatted_key.replace(og, new)

        with open(default_file_path, 'r') as d:
            default = yaml.safe_load(d)

        defSettingPath = default.get('x-spiri-options').get(key)
        settingType = defSettingPath.get('type')

        if 'true' in val.casefold():
            val = True
        elif 'false' in val.casefold():
            val = False
        else:
            try:
                val = float(val)
                if int(val) == val:
                    val = int(val)
            except:
                pass

        # display current settings dynamically
        if settingType == 'bool':
            if val == 1:
                bool_value = True
            else:
                bool_value = False

            def on_toggle(e, k):
                if e.value == True:
                    settings[k] = 1
                else:
                    settings[k] = 0
            
            with ui.row().classes('items-center justify-between w-[35%]'):
                ui.label(f'{formatted_key}:')
                ui.switch(value=bool_value, on_change=lambda e, k=key: on_toggle(e.sender, k))

        elif settingType == ('int' or 'float'):
            min_val = defSettingPath.get('min', None)
            max_val = defSettingPath.get('max', None)
            step = defSettingPath.get('step', None)
            
            def update(e, k):
                if int(e.value) == e.value:
                    settings[k] = int(e.value)
                else:
                    settings[k] = e.value

            ui.number(
                formatted_key, 
                value=val, 
                min=min_val, 
                max=max_val, 
                step=step, 
                on_change=lambda e, k=key: update(e.sender, k)
            )
        else:
            ui.input(formatted_key, value=val, on_change=(lambda e, k=key: settings.update({k: e.value}))).classes('w-full')


@ui.page('/edit_robot')
async def edit_robot(robotID):
    ui.label(f'Edit {robotID}').classes('text-h5')
    display(robotID)

def save_changes(robotID):
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    config_folder_name = f"{robotID}"
    config_folder_path = os.path.join(ROOT_DIR, "data", config_folder_name)
    config_file_path = os.path.join(config_folder_path, "config.env")

    with open(config_file_path, 'w') as f:
        for key, val in settings.items():
            f.write(f'{key}={val}\n')

def clear_changes(robotID):
    display.refresh(robotID)