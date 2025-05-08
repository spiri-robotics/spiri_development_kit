#!/bin/bash
set -e

# Source ROS environment
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "ROS setup file not found at /opt/ros/jazzy/setup.bash"
    exit 1
fi

# Export Gazebo Sim resource path
export GZ_SIM_RESOURCE_PATH=/worlds

# Execute the command passed to the entrypoint
exec "$@"
