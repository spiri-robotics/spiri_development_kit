import asyncio, httpx

from nicegui import ui, run
from nicegui.binding import bind_from
from loguru import logger
from pathlib import Path

from spiriSdk.pages.new_robots import new_robots
from spiriSdk.pages.tools import gz_world
from spiriSdk.ui.ToggleButton import ToggleButton
from spiriSdk.utils.daemon_utils import robots
from spiriSdk.utils.gazebo_utils import get_running_worlds, is_robot_alive
from spiriSdk.utils.InputChecker import InputChecker
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.classes.DinDockerRobot import DinDockerRobot
from spiriSdk.utils.signals import update_cards
# Constants for card layout
half = 'calc(50%-(var(--nicegui-default-gap)/2))'
third = 'calc((100%/3)-(var(--nicegui-default-gap)/1.5))' # formula: (100% / {# of cards}) - ({default gap} / ({# of cards} / {# of gaps}))
card_padding = 'calc(var(--nicegui-default-padding)*1.2)'
# Define the root directory and data directory paths
ROOT_DIR = Path(__file__).parents[2].absolute()
DATA_DIR = ROOT_DIR / 'data'

async def addRobot():
    """Open a dialog to add a new robot."""
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        checker = InputChecker()
        await new_robots(checker)

        async def submit(button):
            button = button.props(add='loading')

            # Import here instead of at the top to get the updated selected_robot
            from spiriSdk.pages.new_robots import selected_robot, selected_options
            await save_robot_config(selected_robot, selected_options, d)

            d.close()

            # Refresh display to update visible cards

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=d.close)
            # Add button is disabled until all input fields have valid values
            ui.button(
                'Add', 
                color='secondary', 
                on_click=lambda e: submit(e.sender)
            ).bind_enabled_from(checker, 'isValid')
    
    d.open()

async def remove_from_world(robot):
    """Remove the robot from the Gazebo world."""
    try:
        result = await robots[robot].unspawn()
        if not result:
            logger.warning(f'Failed to remove {robot} from world')
            return False
        ui.notify(f'Removed {robot} from world', type='positive')
        return True
    except Exception as e:
        logger.warning(e)
        return False
    
async def delete(robot):
    """Delete the robot card and remove the robot from the system."""
    await cards[robot].destroy()
    del cards[robot]
    n = ui.notification(timeout=False)
    for i in range(1):
        n.message = f'Deleting {robot}...'
        n.spinner=True
        await asyncio.sleep(0.1)

    if await delete_robot(robot):
        n.message = f'{robot} deleted'
        n.type = 'positive'
    else:
        n.message = f'error deleting {robot}'
        n.type = 'negative'
    
    n.spinner = False
    n.timeout = 4

cards= {}
            
@ui.refreshable
async def displayCards():
    """Display cards for each robot in the robots dictionary."""
    names = robots.keys()
    for name in names:
        card = RobotCard(name, robots[name])
        cards[name] = card
    with ui.row(align_items='stretch').classes('w-full'):
        for name, card in cards.items():
            await card.render()
            
            
class RobotCard:
    """A card representing a robot with its details and actions."""
    def __init__(self, name, robot):
        self.name = name
        self.config_file = DATA_DIR / self.name / 'config.env'
        self.desc = None
        self.robot: DinDockerRobot = robot
        self.robot_class = None
        self.gz_state = False
        self.gz_visible = False
        self.on = False
        self.last_updated = 2
        self.chips = {}
        with open(self.config_file) as f:
            for line in f:
                if 'DESC' in line:
                    self.desc = line.split('=', 1)
                    self.desc = self.desc[1].strip()
                elif 'ROBOT_CLASS' in line:
                    self.robot_class = line.split('=', 1)
                    self.robot_class = self.robot_class[1].strip()
        self.ip = None
        update_cards.connect(self.listen_to_polling)
    
    @ui.refreshable
    async def render(self):
        """Render the robot card with its details and buttons."""
        status = await self.robot.get_status()
        with ui.card().classes(f'p-[{card_padding}] w-full min-[1466px]:w-[{half}] min-[2040px]:w-[{third}] h-auto'):
            # Key details - name, status, class, description
            with ui.card_section().classes('w-full p-0 pb-2 mb-auto'):
                with ui.row(align_items='center').classes('w-full'):
                    ui.label(f'{self.name}').classes('text-xl font-semibold')
                    with ui.icon('sym_o_info', size='sm'):
                        ui.tooltip(self.robot_class[1:-1]).classes('text-sm')

                    ui.space()

                    self.label_status = ui.label('Status Loading...').classes('text-lg font-semibold')
                    self.chips["Running"] = ui.chip("", color='running', text_color='white').classes('m-0')
                    self.chips["Restarting"] = ui.chip("", color='restarting', text_color='white')
                    self.chips["Exited"] = ui.chip("", color='exited', text_color='white')
                    self.chips["Created"] = ui.chip("", color='created', text_color='white')
                    self.chips["Paused"] = ui.chip("", color='paused', text_color='white')
                    self.chips["Dead"] = ui.chip("", color='dead', text_color='white')
                    
                for chip in self.chips.values():
                    chip.visible = False
                
                await self.update_status()
                                
                if self.desc != None:
                    ui.label(f'{self.desc[1:-1]}').classes('text-base italic text-zinc-700 dark:text-zinc-300')

            # IP and web interface link
            with ui.card_section().classes('w-full p-0'):
                self.ip = ui.markdown(f'**Robot IP:** {self.robot.get_ip()}').classes('text-base')
                self.ip.bind_visibility(self.__dict__, 'on')
            
                # Link to the robot's web interface if applicable 
                # if "spiri_mu" in robotName:
                #     url = f'http://{robots[robotName].get_ip()}:{80}'
                #     ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('py-3')
            
            # Docker host
            with ui.card_section().classes('w-full p-0 mb-6'):
                docker_host = ui.code(f"DOCKER_HOST={self.robot.get_docker_host()}", language='bash').classes('text-zinc-700 dark:text-zinc-300')
                docker_host.bind_visibility(self.__dict__, 'on')   
                             
            # Actions
            with ui.card_section().classes('w-full p-0'):
                with ui.row(align_items='end'):
                    if isinstance(status, dict) and status.get('Running', 0) > 0:
                        self.on = True
                    power = ToggleButton(on_label='power off', off_label='power on', state=self.on)
                    bind_from(self_obj=power, self_name='state', other_obj=self, other_name='on', backward=lambda v: v)
                    
                    reboot_btn = ui.button('Reboot', color='secondary')
                    
                    gz_toggle = ToggleButton(state=self.gz_state, on_label="remove from gz sim", off_label="add to gz sim")
                    bind_from(self_obj=gz_toggle, self_name='state', other_obj=self, other_name='gz_state', backward=lambda v: v)
                    gz_toggle.bind_visibility(self.__dict__, 'gz_visible')
                    
                    ui.space()
                    
                    trash = ui.button(icon='delete', on_click=lambda n=self.name: delete(n), color='negative')
                    
                    buttons = [power, reboot_btn, gz_toggle, trash]
                    
                    power.on_switch = lambda b=buttons: self.power_off(b)
                    power.off_switch = lambda b=buttons: self.power_on(b)
                    reboot_btn.on_click(lambda b=buttons: self.reboot(b))
                    gz_toggle.on_switch = lambda r=self.name: remove_from_world(r)
                    gz_toggle.off_switch = lambda: self.spawn()
    
    async def update_status(self):
        """Update the robot's status and visibility of chips based on the current state."""
        status = await robots[self.name].get_status()
        if isinstance(status, dict):
            self.on = True
            for state in status.keys():
                if status[state] > 0:
                    self.chips[state].visible = True
                    self.chips[state].text = f'{state}: {status.get(state, 0)}'
                else:
                    self.chips[state].visible = False
            self.label_status.visible = False
        else:
            for state in self.chips.keys():
                self.chips[state].visible = False
            self.label_status.visible = True
            self.label_status.text = f'{status.title()}'
            if status.lower() == 'stopped' or status.lower() == 'not created or removed':
                self.on = False
                self.label_status.classes(add='text-[#BF5234]', remove='text-[#666666] dark:text-[#AAAAAA]')
            else: 
                self.on = True
                self.label_status.classes(add='text-[#666666] dark:text-[#AAAAAA]', remove='text-[#BF5234]')
        if self.ip:
            self.ip.content = f'**Robot IP:** {self.robot.get_ip()}'
            
    async def spawn(self):
        """Spawn the robot in the Gazebo world if it is not already alive."""
        if not is_robot_alive(self.name):
            logger.info(f'Spawning {self.name}...')
            n = ui.notification(timeout=None)
            for i in range(1):
                n.message = f'Spawning {self.name}...'
                n.spinner = True
                await asyncio.sleep(1)
            await robots[self.name].spawn()
            n.message = f'{self.name} spawned'
            n.type = 'positive'
            n.spinner = False
            n.timeout = 4
            self.on = True
            self.render.refresh()
    
    async def power_on(self, buttons: list[ui.button]):
        """Power on the robot and update the UI accordingly."""
        for button in buttons:
            button.disable()
            
        logger.info(f'Powering on {self.name}...')
        
        n = ui.notification(timeout=None)
        for i in range(1):
            n.message = f'Powering on {self.name}...'
            n.spinner = True
            await asyncio.sleep(1)
            
        await robots[self.name].start()
        
        n.message = f'{self.name} started'
        n.type = 'positive'
        n.spinner = False
        n.timeout = 4
        self.on = True
        
        self.render.refresh()
    
    async def power_off(self, buttons: list[ui.button]):
        """Power off the robot and update the UI accordingly."""
        logger.info(f'Powering off {self.name}...')
        
        for button in buttons:
            button.disable()
            
        n = ui.notification(timeout=None)
        for i in range(1):
            n.message = f'Powering off {self.name}...'
            n.spinner = True
            await asyncio.sleep(1)
            
        await robots[self.name].stop()
        
        n.message = f"Stopped {self.name}"
        n.type = 'positive'
        n.spinner = False
        n.timeout = 4
        self.on = False
        
        self.render.refresh()
        
    async def reboot(self, buttons: list[ui.button]):
        """Reboot the robot and update the UI accordingly."""
        logger.info(f'Rebooting {self.name}...')
        
        for button in buttons:
            button.disable()
            
        n = ui.notification(message=f'Rebooting {self.name}...', spinner=True, timeout=None)

        await robots[self.name].restart()
        
        n.message = f'{self.name} rebooted'
        n.spinner = False
        n.type = 'positive'
        n.timeout = 4
        self.on = True
        
        self.render.refresh()
        
    async def destroy(self):
        """Disconnect the update_cards signal listener to prevent memory leaks."""
        await run.io_bound(update_cards.disconnect, self.listen_to_polling)
    
    async def listen_to_polling(self, sender, visible=True):
        """Listen to the update_cards signal to update the robot's status and visibility in the Gazebo world."""
        await self.update_status()
        world_running = get_running_worlds()
        if len(world_running) > 0:
            self.gz_visible = True
        else:
            if is_robot_alive(self.name):
                await remove_from_world(self.name)
            self.gz_visible = False
        if not is_robot_alive(self.name):
            self.gz_state = False
        else:
            self.gz_state = True
        if len(world_running) == 0:
            gz_world.models = {}
    