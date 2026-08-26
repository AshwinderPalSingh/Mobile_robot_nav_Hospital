cmake_minimum_required(VERSION 3.8)
project(hospital_delivery_bot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

install(DIRECTORY
  config
  maps
  urdf
  launch
  worlds
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  hospital_delivery_bot/delivery_node.py
  hospital_delivery_bot/simple_teleop.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
