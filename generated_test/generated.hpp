#pragma once

#include <memory>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <tuple>
#include <optional>
#include <variant>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <cmath>

namespace pytocpp {

    class Shape;
    class Rectangle;
    class Circle;

    /**
     * Base class for geometric shapes.
     */
    class Shape {
    public:
        Shape();
        /**
         * Calculate the area of the shape.
         */
        float area() const;
        /**
         * Return a description of the shape.
         */
        str describe() const;

    protected:
    };
    /**
     * A rectangle shape.
     */
    class Rectangle : public Shape {
    public:
        Rectangle();
        /**
         * Calculate the area of the rectangle.
         */
        float area() const;
        /**
         * Return a description of the rectangle.
         */
        str describe() const;

    protected:
    };
    /**
     * A circle shape.
     */
    class Circle : public Shape {
    public:
        Circle();
        /**
         * Calculate the area of the circle.
         */
        float area() const;
        /**
         * Return a description of the circle.
         */
        str describe() const;

    protected:
    };
    double function_calculate_total_area(std::vector<int> shapes);

    std::map<std::string, std::variant<double, std::string>> function_get_shape_info();

    void function_main();

    void function___init__(auto self, double radius, std::string color);

    double function_area(auto self);

    std::string function_describe(auto self);

} // namespace pytocpp
