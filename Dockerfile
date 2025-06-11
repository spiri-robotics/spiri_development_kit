FROM ros:jazzy-ros-base-noble AS base

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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/plugins
ENV GZ_SIM_RESOURCE_PATH=/worlds

FROM base AS devcontainer
ARG USERNAME=USERNAME
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Delete user if it exists in container (e.g Ubuntu Noble: ubuntu)
RUN if id -u $USER_UID ; then userdel `id -un $USER_UID` ; fi

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3-pip
RUN echo "source /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc
ENV SHELL=/bin/bash

# ********************************************************
# * Anything else you want to do like clean up goes here *
# ********************************************************


# [Optional] Set the default user. Omit if you want to keep the default as root.
CMD ["/bin/bash"]

FROM base AS prod

ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

ADD --chown=ubuntu:ubuntu . /app

WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "python", "-m", "spiriSdk.main"]