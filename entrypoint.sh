# Source ROS setup
source /opt/ros/jazzy/setup.bash

# Set the GZ_SIM_RESOURCE_PATH environment variable
export GZ_SIM_RESOURCE_PATH=/worlds

# Execute the passed command
exec "$@"