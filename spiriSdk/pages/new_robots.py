from nicegui import ui
import os
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import yaml
import re
from pathlib import Path
from spiriSdk.utils.new_robot_utils import ensure_options_yaml, ROBOTS_DIR, save_robot_config

robots = ensure_options_yaml()

@ui.page('/new_robots')
async def new_robots():
    await styles()

    selected_robot = {'name': None}
    selected_additions = ["gimbal"]
    selected_options = {}

    def on_select(robot_name: str):
        selected_robot['name'] = robot_name
        display_robot_options(robot_name)
    
    def display_robot_options(robot_name):
        ui.notify(f'Selected Robot: {robot_name}, Selected Addition: {addition}' for addition in selected_additions)
        options_path = os.path.join(ROBOTS_DIR, robot_name, 'options.yaml')
        if not os.path.exists(options_path):
            ui.notify(f"No options.yaml found for {robot_name}")
            return

        with open(options_path, 'r') as yaml_file:
            options = yaml.safe_load(yaml_file)

        # Clear previous options UI
        options_container.clear()

        # Display options dynamically
        with options_container:
            ui.label(f"Options for {robot_name}").classes('text-lg')
            for key, option in options.get('x-spiri-options', {}).items():
                ui.label(key).classes('text-h6')
                ui.label(option.get('help-text', '')).classes('text-body2')
                option_type = option.get('type', 'text')
                if option_type == 'bool':
                    with ui.row():
                        switch_label = ui.label(str(option.get('value', False))).classes('text-body2')
                        def toggle_switch(e):
                            switch_label.set_text(f"{e.value}")
                            selected_options[key] = e.value
                            print(f"Switch {key} changed to {e.value}")
                        switch = ui.switch(
                            value=option.get('value', False),
                            on_change=lambda e: toggle_switch(e),
                        )
                        switch.label = key
                elif option_type == 'int':
                    min_val = option.get('min')
                    max_val = option.get('max')
                    step = option.get('step', 1) or 1
                    current_value = option.get('value', 0)

                    if min_val is not None and max_val is not None:
                        # Generate dropdown choices from min to max using step
                        int_options = list(range(min_val, max_val + 1, step))
                        with ui.select(
                            options=int_options,
                            value=current_value,
                            on_change=(lambda e, k=key: selected_options.update({k: e.value}))
                        ) as dropdown:
                            dropdown.label = key
                    else:
                        # Fallback: no min/max, use input box
                        ui.input(
                            label=f"{key} (integer)",
                            value=str(current_value),
                            on_change=(lambda e, k=key: selected_options.update({k: e.value}))
                        )
                elif option_type == 'text':
                    ui.input(key, value=option.get('value', ''), on_change=(lambda e, k=key: selected_options.update({k: e.value})))
                elif option_type == 'dropdown':
                    # Ensure the dropdown options are a list
                    dropdown_options = option.get('options', [])
                    if isinstance(dropdown_options, list):
                        with ui.dropdown_button(f"{key}: {option.get('value', '')}", auto_close=True):
                            for item in dropdown_options:
                                ui.item(item, on_change=(lambda e, k=key: selected_options.update({k: e.value})))
                    else:
                        ui.label(f"Invalid dropdown options for {key}").classes('text-body2')
                else:
                    ui.input(key, value=option.get('value', ''), on_change=(lambda e, k=key: selected_options.update({k: e.value})))
        
    with ui.card():
        ui.label('New Robot').classes('text-h5')
        ui.label("Select new robot type")
        with ui.dropdown_button("Choose Robot Here", color='secondary', auto_close=True) as dropdown:
            for robot in robots:
                ui.item(robot, on_click=lambda _, r=robot: on_select(r))

        options_container = ui.column()

        ui.button('Add Robot', color='secondary', on_click=lambda: save_robot_config(selected_robot['name'], selected_options)).classes('q-mt-md')
