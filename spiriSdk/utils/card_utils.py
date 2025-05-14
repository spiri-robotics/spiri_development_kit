from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons, init_daemons
from spiriSdk.utils.new_robot_utils import delete_robot
from spiriSdk.pages.tools import tools, prep_bot

class RobotContainer:

    def __init__(self, bigCard, addRobot, editRobot) -> None:
        self.destination = bigCard
        self.addRobot = addRobot
        self.editRobot = editRobot

    async def displayButtons(self) -> None:
        with self.destination:
            with ui.row().classes('justify-items-stretch w-full'):
                ui.button('Add Robot', on_click=self.addRobot.open, color='secondary').classes('text-base')
                ui.space()
                await tools()

    async def displayCards(self) -> None:
        daemons = await init_daemons()  # fetch up-to-date daemons dict
        names = daemons.keys()
        self.addRobot.close()
        self.destination.clear()
        with self.destination:
            await self.displayButtons()
            for robotName in names:
                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5')
                            ui.label(f'active').classes('mt-5')
                        ui.space()
                        with ui.card_actions():
                            ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                            ui.button('Stop', icon='stop', color='warning').classes('m-1')
                            ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                            ui.button("Add robot to world", on_click=lambda: prep_bot(robotName)).classes('m-1 mr-10')

                            async def delete(n):
                                if await delete_robot(n):
                                    ui.notify(f'{n} deleted')
                                    await self.displayCards()
                                else:
                                    ui.notify('error deleting robot')

                            with ui.dropdown_button(icon='settings', color='secondary'):
                                ui.item('Edit', on_click=self.editRobot.open)
                                ui.item('Delete', on_click=lambda n=robotName: delete(n))

    def assignAddRobot(self, addRobot) -> None:
        self.addRobot = addRobot

    def assignEditRobot(self, editRobot) -> None:
        self.editRobot = editRobot
