from nicegui import ui

async def styles():

    ui.colors(
        primary='#9EDFEC', 
        secondary='#274c77',
        accent="#c52e6d",
        dark='#292e32',
        dark_page='#212428',
        positive='#609926',
        negative='#BF5234',
        info='#586469',
        dark_info="#819299",
        warning='#fac529',
        exited="#811D1D",
        restarting="#77400D",
        running="#609926", 
        created="#818307", 
        paused="#0e1977", 
        dead="#000000")
    
    ui.add_css(
        '''
        .nicegui-markdown p {
            margin: 0px;
        }
        '''
    )