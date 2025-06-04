#!/bin/bash
set -e

# Source ROS environment
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "ROS setup file not found at /opt/ros/jazzy/setup.bash"
    exit 1
fi
# Execute the command passed to the entrypoint
exec "$@"
