import os, asyncio, httpx
from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons, display_daemon_status, DaemonEvent
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.pages.tools import tools, gz_world
from spiriSdk.utils.gazebo_utils import get_running_worlds, is_robot_alive
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.ui.ToggleButton import ToggleButton
from spiriSdk.utils.InputChecker import InputChecker

async def is_service_ready(url: str, timeout: float = 0.5) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)            
            return response.status_code == 200
    except Exception:
        return False
    
def copy_text(command):
    ui.run_javascript(f'''
        navigator.clipboard.writeText("{command}");
    ''')
    ui.notify("Copied to clipboard!")
    
async def addRobot():
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        checker = InputChecker()
        await new_robots(checker)

        async def submit(button):
            button = button.props(add='loading')

            # Import here instead of at the top to get the updated selected_robot
            from spiriSdk.pages.new_robots import selected_robot, selected_options
            await save_robot_config(selected_robot, selected_options)

            d.close()

            # Refresh display to update visible cards
            from spiriSdk.pages.home import container
            await container.displayCards()

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=d.close).classes('text-base')
            # Add button is disabled until all input fields have valid values
            ui.button(
                'Add', 
                color='secondary', 
                on_click=lambda e: submit(e.sender)
            ).classes('text-base').bind_enabled_from(checker, 'isValid')
    
    d.open()

class RobotContainer:

    def __init__(self, destination) -> None:
        self.destination = destination
        DaemonEvent.subscribe(self.displayCards)
        self.gz_toggles = {}

    def is_empty(self) -> bool:
        return len(list(self.destination.descendants())) == 0

    async def displayButtons(self) -> None:
        with self.destination:
            with ui.row().classes('justify-items-stretch w-full'):
                ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
                # ui.button(on_click=lambda: ui.navigate.to('/new_robots'), color='secondary').classes('text-base')
                ui.space()
                await tools()

    async def displayCards(self) -> None:
        names = daemons.keys()
        self.destination.clear()
        with self.destination:
            await self.displayButtons()

            for robotName in names:

                ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                DATA_DIR = os.path.join(ROOT_DIR, 'data')
                config_file = os.path.join(DATA_DIR, robotName, 'config.env')
                alias = robotName
                with open(config_file) as f:
                    for line in f:
                        if 'ALIAS' in line:
                            alias = line.split('=', 1)
                            alias = alias[1].strip()
                            break

                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            if alias == robotName or alias == robotName:
                                ui.label(f'{robotName}').classes('mb-5 text-lg font-semibold text-gray-900 dark:text-gray-100')
                            else:
                                ui.label(f'{alias}').classes('text-lg font-semibold text-gray-900 dark:text-gray-100')
                                ui.label(f'{robotName}').classes('mb-5 text-base font-normal text-gray-900 dark:text-gray-100')
                            label_status = ui.label('Status: Loading...').classes('text-sm text-gray-600 dark:text-gray-300')

                            async def update_status(name, label):
                                status = await display_daemon_status(name)
                                label.text = f'Status: {status}'

                            # Initial status
                            await update_status(robotName, label_status)

                            # Periodic update
                            def start_polling(name, label):
                                async def polling_loop():
                                    while True:
                                        await update_status(name, label)
                                        toggle = self.gz_toggles.get(robotName)
                                        if toggle:
                                            if not is_robot_alive(robotName):
                                                toggle._state = True
                                            else:
                                                toggle._state = False
                                            toggle.update()
                                        if await get_running_worlds() == []:
                                            gz_world.models = {}
                                        await asyncio.sleep(5)
                                asyncio.create_task(polling_loop())

                            start_polling(robotName, label_status)
                        ui.space()
                        with ui.card_actions():
                            
                            async def add_to_world(robot=robotName):
                                ip = daemons[robotName].get_ip()
                                # ip = '0.0.0.0'
                                robotType = str(robot).split('-')[0]
                                await gz_world.prep_bot(robot, robotType, ip)
                                ui.notify(f'Added {robot} to world')

                            async def remove_from_world(robot=robotName):
                                robot = gz_world.models[robot].kill_model()
                                
                            toggle = ToggleButton(
                                on_label="add to gz sim", 
                                off_label="remove from gz sim", 
                                on_switch=add_to_world, 
                                off_switch=remove_from_world
                            ).classes('m-1 mr-10 text-base')
                            self.gz_toggles[robotName] = toggle


                            async def delete(n):
                                notif = ui.notification(timeout=False)
                                for i in range(1):
                                    notif.message = 'Deleting...'
                                    notif.spinner=True
                                    await asyncio.sleep(0.1)

                                if await delete_robot(n):
                                    notif.message = f'{n} deleted'
                                    notif.type = 'positive'
                                else:
                                    notif.message = 'error deleting robot'
                                    notif.type = 'negative'
                                
                                notif.spinner = False
                                await asyncio.sleep(4)
                                notif.dismiss()

                            ui.button(icon='delete', on_click=lambda n=robotName: delete(n), color='secondary').classes('text-base')

                    # Display the robot's Docker services command            
                    with ui.card_section():
                        with ui.column():
                            command = f"DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_{robotName}.socket"
                            ui.code(command, language='bash').classes('text-sm text-gray-600 dark:text-gray-200 mb-4')
                            ui.label(f'Robot IP: {daemons[robotName].get_ip()}')
                            
                            # Link to the robot's web interface if applicable
                            if "spiri_mu" in str.join("_", robotName.split("_")[:1]):
                                url = f'http://{daemons[robotName].get_ip()}:{80}'
                                ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm dark:text-gray-200 py-3')
                                        
                            if str.join("_", robotName.split("_")[:1]) == "ARC":
                                url = f'http://{daemons[robotName].get_ip()}:{80}'
                                ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm dark:text-gray-200 py-3')
                                
    def show_loading(self) -> None:
        if len(daemons) == 0:
            pass
        else:
            with self.destination:
                with ui.row(align_items='center').classes('w-full justify-center mt-[20vh]'):
                    ui.spinner(size='40px')
                    ui.label('Starting Containers...').classes('text-base')