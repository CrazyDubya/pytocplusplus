#include "generated.hpp"
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <optional>
#include <variant>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <iostream>
#include <string>
#include <sstream>
#include <cmath>

namespace pytocpp {

Shape::Shape(std::string color) {
    color_ = color;
}

double Shape::area() const {
    return 0.0;}

std::string Shape::describe() const {
    return "A " + color_ + " shape";}

Rectangle::Rectangle(double width, double height, std::string color) : Shape(color) {
    width_ = width;
    height_ = height;
    color_ = color;
}

double Rectangle::area() const {
    return (width_ * height_);}

std::string Rectangle::describe() const {
    return "A " + color_ + " rectangle with width " + std::to_string(width_) + " and height " + std::to_string(height_);}

Circle::Circle(double radius, std::string color) : Shape(color) {
    radius_ = radius;
    color_ = color;
}

double Circle::area() const {
    // Using math constants
    const double pi = M_PI;
    return (pi * pow(radius_, 2));}

std::string Circle::describe() const {
    return "A " + color_ + " circle with radius " + std::to_string(radius_);}

double calculate_total_area(std::vector<Shape> shapes) {
    double total = 0.0;
    for (const auto& shape : shapes) {
        total += shape.area();
    }
    return total;
}

std::map<std::string, std::variant<double, std::string>> get_shape_info(std::variant<Rectangle, Circle> shape) {
    // Create return map with appropriate type for Union values
    std::map<std::string, std::variant<double, std::string>> info;

    // Use visitor pattern to handle different shape types
    std::visit([&info](auto&& s) {
        // Common attributes for all shapes using public interface
        info["area"] = s.area();
        info["description"] = s.describe();

        // Add shape-specific attributes
        if constexpr (std::is_same_v<std::decay_t<decltype(s)>, Rectangle>) {
            info["type"] = std::string("Rectangle");
        } else if constexpr (std::is_same_v<std::decay_t<decltype(s)>, Circle>) {
            info["type"] = std::string("Circle");
        }
    }, shape);

    return info;
}

void main() {
    // Create shapes list
    std::vector<std::variant<Rectangle, Circle>> shapes = {
        Rectangle(5.0, 4.0, "blue"),
        Circle(3.0, "red"),
        Rectangle(2.5, 3.0, "green")
    };

    // Calculate total area
    double total_area = 0.0;
    for (const auto& shape : shapes) {
        std::visit([&total_area](auto&& s) {
            total_area += s.area();
        }, shape);
    }
    std::cout << "Total area of all shapes: " << total_area << std::endl;

    // Get info about each shape
    for (const auto& shape : shapes) {
        std::map<std::string, std::variant<double, std::string>> info = get_shape_info(shape);
        std::cout << "Shape info: [area=" << std::get<double>(info["area"]) << ", description=" << std::get<std::string>(info["description"]) << "]" << std::endl;
    }

    // Optional shape
    std::optional<std::variant<Rectangle, Circle>> optional_shape;
    if (total_area > 50) {
        optional_shape = Rectangle(1.0, 1.0, "white");
    }

    if (optional_shape) {
        double area = 0.0;
        std::visit([&area](auto&& s) {
            area = s.area();
        }, *optional_shape);
        std::cout << "Optional shape area: " << area << std::endl;
    }
    else {
        std::cout << "No optional shape created" << std::endl;
    }
}

} // namespace pytocpp
