import os, asyncio, httpx
from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons, stop_container, start_container, restart_container, display_daemon_status, DaemonEvent
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config, inputChecker
from spiriSdk.pages.tools import tools, gz
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.pages.edit_robot import edit_robot, save_changes, clear_changes

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
        checker = inputChecker()
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
            addBtn = ui.button('Add', color='secondary', on_click=lambda e: submit(e.sender)).classes('text-base')
            addBtn.bind_enabled_from(checker, 'isValid')
    
    d.open()

async def editRobot(robotName, drop: ui.dropdown_button):
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        await edit_robot(robotName)

        def close():
            d.close()
            clear_changes(robotName)
            drop.close()

        async def saveClose(robotName):
            save_changes(robotName)
            close()
            from spiriSdk.pages.home import container
            await container.displayCards()

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', on_click=close, color='secondary').classes('text-base')
            ui.button('Save', on_click=lambda r=robotName: saveClose(r), color='secondary').classes('text-base')
    d.open()



class RobotContainer:

    def __init__(self, destination) -> None:
        self.destination = destination
        DaemonEvent.subscribe(self.displayCards)

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
            worlds = []
            await self.displayButtons()

            n = ui.notification(timeout=None)
            for i in range(4):
                n.message = 'Displaying...'
                n.spinner = True
                await asyncio.sleep(0.5)

            r = 1

            for robotName in names:
                for i in range(1):
                    n.message = f'Displaying robot {r} of {len(names)}'
                    await asyncio.sleep(0.1)

                ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5 text-lg font-semibold text-gray-900 dark:text-gray-100')
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
                                        await asyncio.sleep(5)
                                asyncio.create_task(polling_loop())

                            start_polling(robotName, label_status)
                        ui.space()
                        with ui.card_actions():
                            def make_stop(robot=robotName):
                                message = stop_container(robot)
                                ui.notify(message)

                            async def make_start(robot=robotName):
                                await start_container(robot)

                            async def make_restart(robot=robotName):
                                await restart_container(robot)
                            
                            async def add_to_world(robot=robotName):
                                robotType = str(robot).split('-')[0]
                                world = gz.worlds[gz.running_worlds[0]]
                                await world.prep_bot(robot, robotType)
                                ui.notify(f'Added {robot} to world')
                                
                                                    
                            ui.button('Start', on_click=make_start, icon='play_arrow', color='positive').classes('m-1 text-base')
                            ui.button('Stop', on_click=make_stop, icon='stop', color='warning').classes('m-1 text-base')
                            ui.button('Restart', on_click=make_restart, icon='refresh', color='secondary').classes('m-1 mr-10 text-base')

                            ui.button('Add robot to world', on_click=add_to_world).classes('m-1 mr-10 text-base').props('color=secondary')

                            async def delete(n,):
                                if await delete_robot(n):
                                    ui.notify(f'{n} deleted')
                                else:
                                    ui.notify('error deleting robot')

                            with ui.dropdown_button(icon='settings', color='secondary').classes('text-base') as drop:
                                ui.item('Edit', on_click=lambda n=robotName, d=drop: editRobot(n, d))
                                ui.item('Delete', on_click=lambda n=robotName: delete(n))

                    # Display the robot's Docker services command            
                    with ui.row(align_items="start").classes('w-full'):
                        with ui.card_section():
                            command = f"DOCKER_HOST=unix:///tmp/dind-sockets/spiri_{robotName}.socket"
                            ui.code(command, language='bash').classes('text-sm text-gray-600 dark:text-gray-200')
                        
                    # Display the robot's web interface if applicable
                    if str.join("-", robotName.split("-")[:1]) == "spiri_mu":
                        with ui.card_section():
                            url = f'http://{daemons[robotName].get_ip()}:{80}'
                            loading = ui.spinner(size='lg')
                            i = 0
                            while not await is_service_ready(url) and i < 6:
                                await asyncio.sleep(1)
                                i += 1

                            loading.set_visibility(False)

                            if await is_service_ready(url):
                                ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm text-gray-200 py-3')
                                ui.html(f'<iframe src="{url}" width="1000" height="600"></iframe>')
                            else: 
                                ui.label('Robot GUI unavailable, please try again later').classes('text-sm text-gray-600 dark:text-gray-300')
                    if str.join("-", robotName.split("-")[:1]) == "ARC":
                        with ui.card_section():
                            url = f'http://{daemons[robotName].get_ip()}:{80}'
                            loading = ui.spinner(size='lg')
                            i = 0
                            while not await is_service_ready(url) and i < 6:
                                await asyncio.sleep(1)
                                i += 1

                            loading.set_visibility(False)

                            if await is_service_ready(url):
                                ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm text-gray-200 py-3')
                                ui.html(f'<iframe src="{url}" width="1000" height="600"></iframe>')
                            else: 
                                ui.label('Web interface not available, please try again later').classes('text-sm text-gray-600 dark:text-gray-300')


                n.message = 'Done'
                n.type = 'positive'
                n.spinner = False
                await asyncio.sleep(6)
                n.dismiss()