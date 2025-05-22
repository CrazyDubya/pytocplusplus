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
        Shape(std::string color);
        /**
         * Calculate the area of the shape.
         */
        double area() const;
        /**
         * Return a description of the shape.
         */
        std::string describe() const;
        std::string get_color() const { return color_; }
        const std::string& get_color_ref() const { return color_; }

    protected:
        std::string color_;
    };
    /**
     * A rectangle shape.
     */
    class Rectangle : public Shape {
    public:
        Rectangle(double width, double height, std::string color);
        /**
         * Calculate the area of the rectangle.
         */
        double area() const;
        /**
         * Return a description of the rectangle.
         */
        std::string describe() const;
        double get_width() const { return width_; }
        double get_height() const { return height_; }
        std::string get_color() const { return color_; }
        const std::string& get_color_ref() const { return color_; }

    protected:
        double width_;
        double height_;
        std::string color_;
    };
    /**
     * A circle shape.
     */
    class Circle : public Shape {
    public:
        Circle(double radius, std::string color);
        /**
         * Calculate the area of the circle.
         */
        double area() const;
        /**
         * Return a description of the circle.
         */
        std::string describe() const;
        double get_radius() const { return radius_; }
        std::string get_color() const { return color_; }
        const std::string& get_color_ref() const { return color_; }

    protected:
        double radius_;
        std::string color_;
    };
    double calculate_total_area(std::vector<Shape> shapes);

    std::map<std::string, std::variant<double, std::string>> get_shape_info(std::variant<Rectangle, Circle> shape);

    void main();

} // namespace pytocpp
