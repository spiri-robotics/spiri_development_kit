FROM ros:jazzy-ros-base


RUN apt-get update && apt-get -y install qterminal mesa-utils \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    docker-compose \
    python3.12-venv \
    python3-pip \
    gstreamer1.0-libav \
    gstreamer1.0-gl \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-ros-gz

COPY --from=git.spirirobotics.com/spiri/gazebo-resources:main /plugins /plugins


ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/plugins
ENV GZ_SIM_RESOURCE_PATH=/worlds

ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

USER ubuntu

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ADD --chown=ubuntu:ubuntu . /app
WORKDIR /app
RUN uv sync --locked


CMD ["uv", "run", "python", "-m", "spiriSdk.main"]