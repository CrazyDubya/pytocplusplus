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

int calculate_fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    int a = 0;
    int b = 1;
    for (int i = 2; i < (n + 1); i += 1) {
        a = b;
        b = (a + b);
    }
    return b;}

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
