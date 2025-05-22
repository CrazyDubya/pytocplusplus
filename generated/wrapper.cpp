#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "generated.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_impl, m) {
    m.doc() = "C++ implementations for optimized numerical operations";

    py::class_<pytocpp::Shape> shape(m, "Shape", "Base class for geometric shapes.");
    shape.def(py::init<std::string>());
    shape.def("area", &pytocpp::Shape::area, "Calculate the area of the shape.");
    shape.def("describe", &pytocpp::Shape::describe, "Return a description of the shape.");
    py::class_<pytocpp::Rectangle> rectangle(m, "Rectangle", "A rectangle shape.");
    rectangle.def(py::init<double, double, std::string>());
    rectangle.def("area", &pytocpp::Rectangle::area, "Calculate the area of the rectangle.");
    rectangle.def("describe", &pytocpp::Rectangle::describe, "Return a description of the rectangle.");
    py::class_<pytocpp::Circle> circle(m, "Circle", "A circle shape.");
    circle.def(py::init<double, std::string>());
    circle.def("area", &pytocpp::Circle::area, "Calculate the area of the circle.");
    circle.def("describe", &pytocpp::Circle::describe, "Return a description of the circle.");

    // Note: calculate_total_area and get_shape_info use std::variant which requires special pybind11 handling
    // m.def("calculate_total_area", &pytocpp::calculate_total_area, "Calculate the total area of a list of shapes.");
    // m.def("get_shape_info", &pytocpp::get_shape_info, "Get information about a shape.");
    m.def("main", &pytocpp::main, "Create some shapes and calculate their areas.");
}