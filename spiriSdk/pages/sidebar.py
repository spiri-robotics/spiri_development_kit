from nicegui import ui

def sidebar() -> None:
    """Render the sidebar."""
    with ui.left_drawer(value=True, top_corner=True, bottom_corner=True):
        with ui.column().classes('w-full p-4'):
            with ui.row().classes('items-center justify-between pb-[--nicegui-default-padding]'):
                ui.image("spiriSdk/ui/ConfigUILogo.png").classes('h-12 w-12')
                ui.label('Spiri SDK').classes('text-2xl font-bold')
            ui.button('Dashboard', color='secondary', on_click=lambda: ui.navigate.to("/")).classes('w-full text-left justify-start rounded-none')
            ui.button('Settings', color='secondary', on_click=lambda: ui.navigate.to("/settings")).classes('w-full text-left justify-start rounded-none')