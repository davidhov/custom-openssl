cmake_minimum_required(VERSION 3.5.1)

find_package(Threads)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

add_executable(test_application test.cpp)
target_link_libraries(test_application
	CONAN_PKG::openssl
	Threads::Threads
	${CMAKE_DL_LIBS}
)
