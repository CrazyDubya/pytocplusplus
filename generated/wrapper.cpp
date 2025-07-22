#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "generated.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_impl, m) {
    m.doc() = "C++ implementations for optimized numerical operations";

    m.def("calculate_fibonacci", &pytocpp::calculate_fibonacci, "Calculate the nth Fibonacci number.");
    m.def("main", &pytocpp::main, "None");
}