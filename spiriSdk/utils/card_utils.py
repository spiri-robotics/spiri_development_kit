from nicegui import ui
from spiriSdk.utils.new_robot_utils import daemons
from spiriSdk.utils.new_robot_utils import daemons

class RobotContainer:

    def __init__(self, bigCard) -> None:
        self.destination = bigCard
        self.daemons = ['thing1', 'thing2', 'thing3']

    def displayAddButton(self, addRobot) -> None:
        with self.destination:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')

    def displayCards(self) -> None:
        self.destination.clear()
        with self.destination:
            for robotName in self.daemons:
                with ui.card().classes('w-[calc(50vw-24px)]'):
                    with ui.card_section():
                        ui.label(f'{robotName}').classes('mb-5')
                        ui.label(f'active').classes('mt-5')
                    ui.space()
                    with ui.card_actions():
                        ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                        ui.button('Stop', icon='stop', color='warning').classes('m-1')
                        ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                        with ui.dropdown_button(icon='settings', color='secondary'):
                            ui.item('Edit', on_click=editRobot.open)
                            ui.item('Delete')

    def remove_card(self, robotName) -> None:
        self.card.delete(robotName)

    def display(self, addRobot, bigCard) -> None:
        self.main = bigCard
        with self.main:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')
