# **Welcome to the Spiri SDK!**

The Spiri Robotics Software Development Kit provides a pre-packaged and
easy-to-deploy simulation environment. If you\'re familiar with tools
like Gazebo, ROS, and ArduPilot, you\'ve probably worked with similar
simulation environments in the past.

What makes the Spiri SDK different:

-   **Heavy use of Docker:** each robot gets its own Docker daemon,
    allowing you to simulate your full software stack.

-   **Focus on multi-robot simulation:** the Spiri SDK includes support
    for heterogeneous robot flocks. You could easily deploy ground-based
    robots alongside flying robots, or see if your code works on mixed
    flocks with PX4 and ArduPilot-based robots.

We\'ve provided a few sample robots, located in the robots folder in
your SDK install. You can customize those robots to your liking.

The SDK makes use of several external projects and resources, each with
their own IP policy and licensing:

-   **SpiriRobotUI:** A robot configuration tool running on Spiri robots. It 
    makes it easy to install new apps on a Spiri robot, configure them, 
    and look at information about them. It is essentially a Docker 
    service manager with some extra drone-related configuration options.

-   **Companion-Computer-Commands system:** This system includes two components. The 
    first is a user-space tool that translates MAVLink messages into ROS service calls. 
    The second is a small modification to ArduPilot so that it forwards these MAVLink 
    commands to the companion computer properly.

-   **Docker:** We use custom Docker builds for the third-party projects MAVProxy
    and MAVROS2.

-   **Gazebo-ArduPilot** We have a small fork of Gazebo-ArduPilot that allows it to work with
    Docker-in-Docker deployments.

-   **ROS:** We have a project template for creating new ROS projects, which
    includes options for templates that work with our
    Companion-Computer-Commands system.

# **Installing the Spiri SDK**

The Spiri SDK can be installed by running the following command in a
terminal:

`git clone https://github.com/spiri-robotics/spiri_development_kit.git`

# **Running the Spiri SDK**

Run the Spiri SDK by opening the spiriSdk folder in VS Code and
installing the Dev Containers extension. Reopen the project in 
Dev Containers by hitting Ctrl+Shift+p and clicking **Dev Containers:
Rebuild and Reopen in Container**.

You can then use `uv run python -m spiriSdk.main` to launch the project.

Running using `docker compose` instead of a development environment is a roadmap feature.

# **Using the Spiri SDK**

The Spiri SDK provides a range of functionality. Here are some of the
most common ways to use it.

## **Configuring Authentication Settings**

Upon app startup, a new browser tab will appear with your Spiri SDK UI.

You can configure your authentication settings by navigating to the
Settings page, then following the instructions to add your Gitea
credentials.

![](./docs/readme_img/media/image5.png)

## **Adding a Robot**

1. Navigate to the Dashboard and click **Add Robot**.

2. Select your preferred robot type and configure it with the desired
settings. 

3. Click **Add**.

Your robot should be added after a few seconds, and its service statuses
should be displayed in the top right corner of its card. The robot is 
ready when 3 services are running.

![](./docs/readme_img/media/image2.png)

## **Running a Gazebo Sim**

1. Click **Launch Gazebo** in the top right corner.

2. Select your desired world to run from the dropdown menu, 
then hit **Start World**.

The robot cards should soon display an **Add to GZ Sim** button, which can
be clicked to add each robot to the simulation.

![](./docs/readme_img/media/image6.png)

![](./docs/readme_img/media/image7.png)

## **Controlling a simulated robot with QGroundControl**

1.  In order to control a simulated robot, first ensure it has been
    added to a Gazebo simulation.

2.  Ensure you have installed QGroundControl and run it on your
    local machine.

    Instructions for installing QGC can be found [here.](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html)

3.  In QGroundControl, click on the Q in the top left corner, then
    navigate to Application Settings -\> Comm Links -\> Add Link.

4.  Name your comm link as you see fit, then:

    a.  Check the box labeled **Automatically Connect on Start**.

    b.  Set the Type to **TCP**.

    c.  Ensure the server address matches the IP displayed
        on the robot's card.

    d.  Ensure the Port is set to 5760.

5.  Click **OK**, then select your newly created comm link and click
    **Connect**.

6.  Click **Back** to return to the map view, and you should be connected to
    your simulated robot.

7.  Repeat this process for as many robots as desired.

![](./docs/readme_img/media/image1.png)

## **Stopping, Starting, and Restarting a Robot**

Each robot can be stopped, started, and restarted using the buttons on
its display card. This can be helpful when a robot's services have not 
started up correctly, or if it is having trouble connecting to the simulation. 
The power button toggles the robot on and off, and the reboot button serves
as an easy way to turn the robot off and back on again with just one
click.

![](./docs/readme_img/media/image3.png)

## **Deleting a Robot**

Deleting a robot can be done by clicking the trash can icon in the 
bottom-right corner of its display card. Wait a moment for the success 
message to display and its card to be removed.

## **Inspecting a Robot's Services**

A robot's services can easily be inspected with Lazydocker using the socket provided in the
robot's display card.

Once Lazydocker is installed, simply open a terminal and paste the robot's
socket followed by "lazydocker". It should look something like this:

`DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_spiri_mu_1.socket lazydocker`

Lazydocker can be installed as per their instructions [here.](https://github.com/jesseduffield/lazydocker#installation)

![](./docs/readme_img/media/image4.png)

# **Developer Instructions**

We recommended developing using VS Code and the Dev Containers
extension. After adding a robot, you will see the variables you need to
use to connect to the virtual robot\'s Docker instance.

You can use them to either create a Docker context or run
`DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_your_robot.socket` in
a terminal.

The DOCKER_HOST environment variable will work with any Docker commands,
including third-party ones like Lazydocker:

`DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_your_robot.socket lazydocker`

To begin:

1.  [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

2.  [Install Docker](https://docs.docker.com/engine/install/)

3.  Clone the repository on your local machine.

4.  Open the project in VS Code.

5.  Go to the Extensions tab and search for Dev Containers.

6.  Install the Dev Containers extension and activate it.

7.  Create a .env file in the root of your project with the contents of
    the provided default.env file, then fill in your Spiri-Gitea
    username and token:

    a.  In Gitea, go to Settings -\> Applications

    b.  Name a new token and give it read permissions for both packages
        and repos.

    c.  Click **Generate Token** and copy the resulting token printed at the
        top of the page. It is recommended to store this token somewhere
        safe, as it won't be viewable again.

8.  Hit Ctrl+Shift+p and select **Dev Containers: Rebuild and Reopen in
    Container**.

9.  Open a new terminal in the project folder and follow the Quickstart
    instructions below.

## **Quickstart**

Run the main code: `uv run python -m spiriSdk.main`

Run tests: `uv run pytest`

## **Exiting the Dev Container**

Simply hit Ctrl+Shift+p again in VS Code and select **Dev Containers:
Reopen Folder Locally**

## **Common Issues**

-   Watchfiles sometimes has trouble with authentication, which may produce
    a large red error whenever the app is started or restarted. It also may 
    cause the app to not automatically restart when a file is saved. To fix 
    this, add the following line to the end of the .env file in the root of 
    your project:

    `WATCHFILES_IGNORE_PERMISSION_DENIED="True"`

## **Project Templates**

We have the following project templates available for getting started
quickly with our SDK:

-   A generic ROS2 template:
    https://git.spirirobotics.com/Spiri/template-ros2-pkg

All of our templates use Copier. Please see the [copier
documentation](https://copier.readthedocs.io/en/stable/#installation)
for installation instructions.
