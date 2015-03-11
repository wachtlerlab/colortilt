# - Try to find IRIS
# Once done this will define
#  IRIS_FOUND - System has Iris
#  IRIS_INCLUDE_DIRS - The Iris include directories
#  IRIS_LIBRARIES - The libraries needed to use Iris


find_path(IRIS_INCLUDE_DIR iris.h
  HINTS /usr/local/include
        /usr/include
        $ENV{IRIS_ROOT}/lib
        PATH_SUFFIXES iris)

find_library(IRIS_LIBRARY NAMES iris libiris
       HINTS /usr/local/lib
             /usr/lib
             ${IRIS_INCLUDE_DIR}/../lib
             ${IRIS_INCLUDE_DIR}/../build)

set(IRIS_LIBRARIES ${IRIS_LIBRARY})
set(IRIS_INCLUDE_DIRS ${IRIS_INCLUDE_DIR})

include(FindPackageHandleStandardArgs)
# handle the QUIETLY and REQUIRED arguments and set IRIS_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args(Iris DEFAULT_MSG IRIS_LIBRARY IRIS_INCLUDE_DIR)

mark_as_advanced(IRIS_INCLUDE_DIR IRIS_LIBRARY)

