
# Developing for the SDK

The Spiri Robotics Software Development Kit provides a pre-oackaged and easy to deploy simulation environment.
If you're familiar with tools like gazebo, ROS, and Ardupilot you've probably worked with similar simulation
environments in the past.

What makes the Spiri SDK different is

 * Heavy use of docker, each robot gets it's own docker-daemon allowing you to simulate your full software
 stack.
 * Focus on multi-robot simulation, including heterogenous robot flocks. You could easily deploy ground-based
 robots along-side flying robots, or see if your code works on mixed flocks with PX4 and Ardupilot based robots

We've provided a few sample robots, located in the robots folder in your SDK install. You can customize those
robots to your liking.

We recomended developing using vscode and the "containers" extention. When spawning a robot you will see the variables
you need to set to connect to the virtual robot's docker instance. You can use that to either create a docker context,
or run `DOCKER_HOST=your_robot_path vscode` in a terminal. The `DOCKER_HOST` environment variable will work with
any docker commands, including third-party ones like lazydocker.


# Developing the SDK

## Prerequisites

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Install `docker`: https://docs.docker.com/engine/install/
- Create a .env file in the root of your project and copy in the contents of the default.env file, then fill in your spiri-gitea username and token
    - A gitea access token can be generated on gitea by clicking on your profile picture -> Settings -> Applications, naming a token and giving it read permissions for both packages and repos, then hitting Generate Token, and copying the resulting token printed at the top of the page

## Quickstart

```bash
uv run python -m spiriSdk.main #Run the main code
uv run pytest #Run tests
docker compose up --build #Run in docker
```

## Notes

- To fix the big angry red error that will likely show up on startup, put the following line in the .env file in the root of your project, after "REGISTRIES=[...]" and "AUTH_REGISTRIES=[...]":
    - WATCHFILES_IGNORE_PERMISSION_DENIED="True"
