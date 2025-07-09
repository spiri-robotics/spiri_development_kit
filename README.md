# **Welcome to the Spiri-SDK!**

The Spiri Robotics Software Development Kit provides a pre-packaged and
easy-to-deploy simulation environment. If you\'re familiar with tools
like Gazebo, ROS, and Ardupilot, you\'ve probably worked with similar
simulation environments in the past.

What makes the Spiri-SDK different:

-   **Heavy use of Docker -** each robot gets its own Docker daemon,
    allowing you to simulate your full software stack.

-   **Focus on multi-robot simulation -** the Spiri SDK includes support
    for heterogeneous robot flocks. You could easily deploy ground-based
    robots alongside flying robots, or see if your code works on mixed
    flocks with PX4 and Ardupilot-based robots.

We\'ve provided a few sample robots, located in the robots folder in
your SDK install. You can customize those robots to your liking.

The SDK makes use of several external projects and resources, each with
their own IP policy and licensing.

-   SpiriRobotUI: A robot configuration tool running on spiri robots. It
    makes it easy to install new apps on a Spiri Robot, configure them,
    and look at information about them. It is essentially a docker
    service manager with some extra drone-related configuration option.

-   The Companion-Computer-Commands system includes two components. The
    first is a user-space tool that translates mavlink messages into ROS
    service calls. The second is a small modification to ardupilot so
    that it forwards these mavlink commands to the companion computer
    properly.

-   We use custom docker builds for the third-party projects mavproxy
    and mavros2.

-   We have a small fork of gazebo-ardupilot that makes it work with
    docker-in-docker deployments.

-   We have a project template for creating new ROS projects, it
    includes options for project templates that work with our
    Companion-Computer-Commands system

# **Installing the Spiri-SDK**

The Spiri-SDK can be installed by running the following command in a
terminal:

`git clone https://github.com/spiri-robotics/spiri_development_kit.git`

# **Running the Spiri-SDK**

Run the Spiri-SDK by opening the spiriSdk folder in VScode,
installing the "Dev Containers" extension, and reopening in devcontainers.

You can then use the command `uv run python -m spiriSdk.main` to launch the project.

Running using docker compose instead of a development environment is a roadmap feature.

# **Using the Spiri-SDK**

The Spiri-SDK provides a range of functionality. Here are some of the
most common ways to use it.

## **Configuring Authentication Settings**

Upon App Startup, a new browser tab will appear with your Spiri-SDK UI.

You can configure your Authentication Settings by navigating to the
Settings page, then following the instructions to save your Gitea
Credentials.![](./docs/readme_img/media/image5.png)

## **Adding a Robot**

![](./docs/readme_img/media/image2.png)

To add a Robot, navigate to the Dashboard and click "Add Robot".

Select your preferred robot type and configure it with the desired
settings, then click Add.

Your robot should be added after a few seconds, and service statuses
should be displayed in the top right of its card.

The robot is ready when 3 services are running.

## **Running a Gazebo Sim**

To run a Gazebo Sim, begin by clicking the "Launch Gazebo" button.

From the Dropdown menu, select your desired world to run, then hit
"Start World".

The robot cards should then display an "Add to GZ Sim" button, which can
be clicked to add each robot to the simulation.

![](./docs/readme_img/media/image6.png)

![](./docs/readme_img/media/image7.png)


## **Controlling a simulated robot with QGroundControl**

1.  In order to control a simulated robot, first ensure it has been
    added to a Gazebo simulation.

2.  Then, ensure you have installed QGroundControl and run it on your
    local machine.

    Note: Instructions for installing QGC can be found here: https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html

3.  In QGroundControl, click on the Q in the top left corner, then
    navigate to Application Settings -\> Comm Links -\> Add Link.

4.  Name your comm link as you see fit, then:

    a.  Check the box labeled "Automatically Connect on Start"

    b.  Set the Type to "TCP"

    c.  Ensure the Server Address matches the IP of the Robot displayed
        on its card

    d.  Ensure the Port is set to 5760

5.  Next, click OK, then select your newly created comm link and click
    "Connect".

6.  Navigate with "Back" to the map view, and you should be connected to
    your simulated robot.

7.  Repeat this for as many robots as desired.

![](./docs/readme_img/media/image1.png)


## **Stopping, Starting, and Restarting a Robot**

Each robot can be stopped, started, and restarted using the buttons on
its display card.

This can be helpful when a robot's services have not started up
correctly, or it is having trouble connecting to the simulation. The
power button toggles the robot on and off, and the reboot button serves
as an easy way to turn the robot off, then back on again with just one
click.

![](./docs/readme_img/media/image3.png)


## **Deleting a Robot**

Deleting a Robot can be done by clicking the trash can icon on its
display card and waiting a moment for the success message to display and
its card to be removed.

## **Inspecting a Robot's Services**

![](./docs/readme_img/media/image4.png)

A robot's services can be inspected using the socket provided in the
robot's display card.

Inspecting the services can be made easy using lazydocker.

Once lazydocker is installed, simply open a terminal, paste the robot's
socket followed by "lazydocker".

It should look something like this:

DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_spiri_mu_1.socket
lazydocker

Lazydocker can be installed as per their instructions here: https://github.com/jesseduffield/lazydocker#installation

# **Developer Instructions**

We recommended developing using VS Code and the "Dev Containers"
extension. After adding a robot, you will see the variables you need to
use to connect to the virtual robot\'s Docker instance.

You can use them to either create a Docker context or run
DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_your_robot.socket code in
a terminal.

The DOCKER_HOST environment variable will work with any docker commands,
including third-party ones like Lazydocker:

DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_your_robot.socket
lazydocker

To begin:

1.  Install uv:
    [[https://docs.astral.sh/uv/getting-started/installation/]{.underline}](https://docs.astral.sh/uv/getting-started/installation/)

2.  Install docker:
    [[https://docs.docker.com/engine/install/]{.underline}](https://docs.docker.com/engine/install/)

3.  Clone the repository on your local machine.

4.  Open the project in VS Code.

5.  Go to the extensions tab and search for Devcontainers.

6.  Install the Devcontainers extension and activate it.

7.  Create a .env file in the root of your project with the contents of
    the provided default.env file, then fill in your Spiri-Gitea
    username and token:

    a.  In Gitea, go to Settings -\> Applications

    b.  Name a new token and give it read permissions for both packages
        and repos.

    c.  Click Generate Token and copy the resulting token printed at the
        top of the page. It is recommended to store this token somewhere
        safe, as it won't be viewable again.

8.  Hit Ctrl+Shift+p and select "Dev Containers: Rebuild and Reopen in
    Container".

9.  Open a new terminal in the project folder and follow the Quick Start
    Instructions below.

## **Quickstart**

Run the main code: uv run python -m spiriSdk.main

Run tests: uv run pytest

## **Exiting the Dev Container**

Simply hit Ctrl+Shift+p again in VScode and select "Dev Containers:
Reopen Folder Locally"

## **Common Issues**

-   Watchfiles sometimes has trouble with authentication, which produces
    a large red error whenever a file is saved and the app is restarted.
    It also may cause the app to not automatically restart when a file
    is saved. To fix this, add the following line to the end of the .env
    file in the root of your project:

> WATCHFILES_IGNORE_PERMISSION_DENIED=\"True\"

## **Project Templates**

We have the following project templates available for getting started
quickly with our SDK

-   A generic ros2 template:
    [https://git.spirirobotics.com/Spiri/template-ros2-pkg](https://git.spirirobotics.com/Spiri/template-ros2-pkg)

All of our templates use Copier. Please see the [copier
documentation](https://copier.readthedocs.io/en/stable/#installation)
for installation instructions.
