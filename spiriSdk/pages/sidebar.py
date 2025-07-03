from nicegui import ui

def sidebar() -> None:
    """Render the sidebar."""
    with ui.left_drawer(value=True, top_corner=True, bottom_corner=True).props('width=250 breakpoint=200 bordered'):
        with ui.column().classes('w-full p-2'):
            with ui.row(align_items='center').classes('w-full justify-between pb-2'):
                ui.image("spiriSdk/ui/Spiri_logo_Mixed_dual_background.svg").classes('h-16 w-16')
                ui.label('Spiri SDK').classes('text-2xl font-semibold')
            ui.button('Dashboard', color='secondary', on_click=lambda: ui.navigate.to("/")).classes('w-full')
            ui.button('Settings', color='secondary', on_click=lambda: ui.navigate.to("/settings")).classes('w-full')