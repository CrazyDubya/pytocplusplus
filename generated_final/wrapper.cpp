#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "generated.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_impl, m) {
    m.doc() = "C++ implementations for optimized numerical operations";

    m.def("function_calculate_fibonacci", &pytocpp::function_calculate_fibonacci, "");
    m.def("function_main", &pytocpp::function_main, "");
}