cmake_minimum_required(VERSION 2.8.4)
project(pp-color-tilt)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -Wall")

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

########################################
# Boost

set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
find_package(Boost 1.49.0 REQUIRED program_options)

include_directories(${Boost_INCLUDE_DIR})
set(LINK_LIBS ${LINK_LIBS} ${Boost_LIBRARIES})

########################################
# OpenGL + Co
find_package(OpenGL REQUIRED)
find_package(GLM REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(GLFW REQUIRED glfw3)

include_directories(${GLFW_INCLUDE_DIRS}
                    ${GLM_INCLUDE_DIRS}
                    ${OpenGL_INCLUDE_DIRS})

link_directories(${GLFW_LIBRARY_DIRS}
                 ${GLM_LIBRARY_DIRS}
                 ${OpenGL_LIBRARY_DIRS})

set(LINK_LIBS ${LINK_LIBS} ${OPENGL_LIBRARIES} ${GLFW_LIBRARIES})

########################################
# IRIS

find_package(IRIS REQUIRED)
include_directories (${IRIS_INCLUDE_DIRS})
set (LINK_LIBS ${LINK_LIBS} ${IRIS_LIBRARIES})

#########################################
# Linux

if(NOT APPLE)
  pkg_search_module(GLEW REQUIRED glew)
  include_directories(${GLEW_INCLUDE_DIRS})
  link_directories(${GLEW_LIBRARY_DIRS})
  set(LINK_LIBS ${LINK_LIBS} ${GLEW_LIBRARIES})

  set(LINK_LIBS ${LINK_LIBS} -lstdc++ -lm)
endif()

#########################################
set(experiment_SOURCES stimulus.h scene.h scene.cc main.cc stimulus.cc)
add_executable(pp-ct ${experiment_SOURCES})
target_link_libraries(pp-ct ${LINK_LIBS})

set(stimgen_SOURCES stimgen.cc stimulus.h stimulus.cc)
add_executable(pp-ct-stimgen ${stimgen_SOURCES})
target_link_libraries(pp-ct-stimgen ${LINK_LIBS})

set(flicker_SOURCES scene.h scene.cc flicker.cc)
add_executable(pp-flicker ${flicker_SOURCES})
target_link_libraries(pp-flicker ${LINK_LIBS})