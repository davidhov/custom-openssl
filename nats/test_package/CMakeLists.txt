cmake_minimum_required(VERSION 3.5.1)
project(test_application CXX)

find_package(nats CONFIG REQUIRED)

add_executable(test_application test.cpp)

target_link_libraries(test_application nats::nats)
