async def on_startup():
    global daemons
    daemons = await init_daemons(daemons or {})