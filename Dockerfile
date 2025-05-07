FROM osrf/ros:jazzy-desktop-full


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
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "python", "-m", "spiriSdk.main"]