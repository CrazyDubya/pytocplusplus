"""Simple example of a class for PyToC++ conversion."""

from typing import List, Optional, Union, Dict

class Shape:
    """Base class for geometric shapes."""
    
    def __init__(self, color: str = "white"):
        self.color = color
    
    def area(self) -> float:
        """Calculate the area of the shape."""
        return 0.0
    
    def describe(self) -> str:
        """Return a description of the shape."""
        return f"A {self.color} shape"


class Rectangle(Shape):
    """A rectangle shape."""
    
    def __init__(self, width: float, height: float, color: str = "white"):
        super().__init__(color)
        self.width = width
        self.height = height
    
    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height
    
    def describe(self) -> str:
        """Return a description of the rectangle."""
        return f"A {self.color} rectangle with width {self.width} and height {self.height}"


class Circle(Shape):
    """A circle shape."""
    
    def __init__(self, radius: float, color: str = "white"):
        super().__init__(color)
        self.radius = radius
    
    def area(self) -> float:
        """Calculate the area of the circle."""
        import math
        return math.pi * self.radius ** 2
    
    def describe(self) -> str:
        """Return a description of the circle."""
        return f"A {self.color} circle with radius {self.radius}"


def calculate_total_area(shapes: List[Shape]) -> float:
    """Calculate the total area of a list of shapes."""
    return sum(shape.area() for shape in shapes)


def get_shape_info(shape: Union[Rectangle, Circle]) -> Dict[str, Union[float, str]]:
    """Get information about a shape."""
    info = {
        "color": shape.color,
        "area": shape.area(),
        "description": shape.describe()
    }
    
    if isinstance(shape, Rectangle):
        info["width"] = shape.width
        info["height"] = shape.height
    elif isinstance(shape, Circle):
        info["radius"] = shape.radius
    
    return info


def main():
    """Create some shapes and calculate their areas."""
    shapes: List[Shape] = [
        Rectangle(5.0, 4.0, "blue"),
        Circle(3.0, "red"),
        Rectangle(2.5, 3.0, "green")
    ]
    
    # Calculate total area
    total_area = calculate_total_area(shapes)
    print(f"Total area of all shapes: {total_area}")
    
    # Get info about each shape
    for shape in shapes:
        info = get_shape_info(shape)
        print(f"Shape info: {info}")
    
    # Optional shape
    optional_shape: Optional[Shape] = Rectangle(1.0, 1.0) if total_area > 50 else None
    if optional_shape:
        print(f"Optional shape area: {optional_shape.area()}")
    else:
        print("No optional shape created")


if __name__ == "__main__":
    main()