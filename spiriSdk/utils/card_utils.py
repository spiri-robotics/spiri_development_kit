from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons
from spiriSdk.utils.new_robot_utils import delete_robot
from spiriSdk.pages.tools import prep_bot

class RobotContainer:

    def __init__(self, bigCard, addRobot, editRobot) -> None:
        self.destination = bigCard
        self.addRobot = addRobot
        self.editRobot = editRobot

    def displayAddButton(self) -> None:
        with self.destination:
            ui.button('Add Robot', on_click=self.addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')

    def displayCards(self) -> None:
        global daemons
        print(daemons.keys())
        self.addRobot.close()
        self.destination.clear()
        with self.destination:
            self.displayAddButton()
            for robotName in daemons:
                with ui.card().classes('w-[calc(50vw-24px)]'):
                    with ui.card_section():
                        ui.label(f'{robotName}').classes('mb-5')
                        ui.label(f'active').classes('mt-5')
                    ui.space()
                    with ui.card_actions():
                        ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                        ui.button('Stop', icon='stop', color='warning').classes('m-1')
                        ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                        def delete():
                            delete_robot()
                            self.displayCards() 

                        with ui.dropdown_button(icon='settings', color='secondary'):
                            ui.item('Edit', on_click=self.editRobot.open)
                            ui.item('Delete', on_click=delete)

    def assignAddRobot(self, addRobot) -> None:
        self.addRobot = addRobot

    def assignEditRobot(self, editRobot) -> None:
        self.editRobot = editRobot
