#include "generated.hpp"
#include <iostream>
#include <vector>

int main() {
    // Test the Fibonacci calculation
    std::vector<int> numbers = {5, 10, 15};
    std::vector<int> results;

    for (int num : numbers) {
        int result = pytocpp::calculate_fibonacci(num);
        results.push_back(result);
        std::cout << "Fibonacci(" << num << ") = " << result << std::endl;
    }

    return 0;
}