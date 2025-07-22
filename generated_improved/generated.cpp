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

int function_calculate_fibonacci(int n) {
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

void function_main() {
    std::vector<int> numbers = std::vector<int>{5, 10, 15};
    std::vector<int> results = std::vector<int>{};
    for (auto num : numbers) {
        auto result = calculate_fibonacci(num);
        results.push_back(result);
        std::cout << "Fibonacci(" + std::to_string(num) + ") = " + result << std::endl;
    }}

} // namespace pytocpp
