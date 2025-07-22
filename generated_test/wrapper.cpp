#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "generated.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_impl, m) {
    m.doc() = "C++ implementations for optimized numerical operations";

    py::class_<pytocpp::Shape> shape(m, "Shape", "Base class for geometric shapes.");
    shape.def(py::init<>());
    shape.def("area", &pytocpp::Shape::area, "Calculate the area of the shape.");
    shape.def("describe", &pytocpp::Shape::describe, "Return a description of the shape.");
    py::class_<pytocpp::Rectangle> rectangle(m, "Rectangle", "A rectangle shape.");
    rectangle.def(py::init<>());
    rectangle.def("area", &pytocpp::Rectangle::area, "Calculate the area of the rectangle.");
    rectangle.def("describe", &pytocpp::Rectangle::describe, "Return a description of the rectangle.");
    py::class_<pytocpp::Circle> circle(m, "Circle", "A circle shape.");
    circle.def(py::init<>());
    circle.def("area", &pytocpp::Circle::area, "Calculate the area of the circle.");
    circle.def("describe", &pytocpp::Circle::describe, "Return a description of the circle.");

    m.def("function_calculate_total_area", &pytocpp::function_calculate_total_area, "");
    m.def("function_get_shape_info", &pytocpp::function_get_shape_info, "");
    m.def("function_main", &pytocpp::function_main, "");
    m.def("function___init__", &pytocpp::function___init__, "");
    m.def("function_area", &pytocpp::function_area, "");
    m.def("function_describe", &pytocpp::function_describe, "");
}