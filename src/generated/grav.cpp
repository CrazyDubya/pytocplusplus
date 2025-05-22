#include <iostream>
#include <vector>
#include <cmath>
#include <random>
#include <chrono>
#include <thread>
#include <iomanip>

constexpr double G = 6.67430e-11;  // Gravitational constant

class Vector2D {
public:
    double x, y;

    Vector2D(double x = 0.0, double y = 0.0) : x(x), y(y) {}

    Vector2D operator+(const Vector2D& other) const {
        return Vector2D(x + other.x, y + other.y);
    }

    Vector2D operator-(const Vector2D& other) const {
        return Vector2D(x - other.x, y - other.y);
    }

    Vector2D operator*(double scalar) const {
        return Vector2D(x * scalar, y * scalar);
    }

    Vector2D operator/(double scalar) const {
        return Vector2D(x / scalar, y / scalar);
    }

    double magnitude() const {
        return std::hypot(x, y);
    }

    Vector2D normalize() const {
        double mag = magnitude();
        if (mag == 0) return Vector2D();
        return *this / mag;
    }

    double distance_to(const Vector2D& other) const {
        return (*this - other).magnitude();
    }

    friend std::ostream& operator<<(std::ostream& os, const Vector2D& v) {
        os << "(" << std::scientific << std::setprecision(2) << v.x << ", " << v.y << ")";
        return os;
    }
};

class Particle {
public:
    int id;
    Vector2D position;
    Vector2D velocity;
    double mass;
    Vector2D force;

    Particle(int id, const Vector2D& position, const Vector2D& velocity, double mass)
        : id(id), position(position), velocity(velocity), mass(mass), force() {}

    void apply_force(const Vector2D& f) {
        force = force + f;
    }

    void update(double dt) {
        Vector2D acceleration = force / mass;
        velocity = velocity + acceleration * dt;
        position = position + velocity * dt;
        force = Vector2D();  // reset force
    }

    friend std::ostream& operator<<(std::ostream& os, const Particle& p) {
        os << "[#" << p.id << " m=" << std::scientific << std::setprecision(2) << p.mass 
           << " pos=" << p.position << " vel=" << p.velocity << "]";
        return os;
    }
};

class Simulation {
private:
    std::vector<Particle> particles;
    double time;
    double bounds;
    std::mt19937 rng;

public:
    Simulation(int num_particles, double bounds = 1e9)
        : time(0.0), bounds(bounds), rng(std::random_device{}()) {
        
        std::uniform_real_distribution<double> pos_dist(-bounds, bounds);
        std::uniform_real_distribution<double> vel_dist(-1000, 1000);
        std::uniform_real_distribution<double> mass_dist(1e20, 1e24);

        for (int i = 0; i < num_particles; ++i) {
            Vector2D position(pos_dist(rng), pos_dist(rng));
            Vector2D velocity(vel_dist(rng), vel_dist(rng));
            double mass = mass_dist(rng);
            particles.emplace_back(i, position, velocity, mass);
        }
    }

    void compute_gravitational_forces() {
        size_t n = particles.size();
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                Particle& pi = particles[i];
                Particle& pj = particles[j];
                Vector2D displacement = pj.position - pi.position;
                double distance = displacement.magnitude() + 1e-5;  // Avoid div-by-zero
                double force_magnitude = G * pi.mass * pj.mass / (distance * distance);
                Vector2D force_dir = displacement.normalize();
                Vector2D force = force_dir * force_magnitude;
                pi.apply_force(force);
                pj.apply_force(force * -1);
            }
        }
    }

    void handle_collisions(double merge_distance = 1e6) {
        std::vector<bool> merged(particles.size(), false);
        std::vector<Particle> new_particles;

        for (size_t i = 0; i < particles.size(); ++i) {
            if (merged[i]) continue;
            
            Particle& pi = particles[i];
            bool did_merge = false;

            for (size_t j = i + 1; j < particles.size(); ++j) {
                if (merged[j]) continue;
                
                Particle& pj = particles[j];
                if (pi.position.distance_to(pj.position) < merge_distance) {
                    // Merge particles
                    double total_mass = pi.mass + pj.mass;
                    Vector2D new_pos = (pi.position * pi.mass + pj.position * pj.mass) / total_mass;
                    Vector2D new_vel = (pi.velocity * pi.mass + pj.velocity * pj.mass) / total_mass;
                    new_particles.emplace_back(pi.id, new_pos, new_vel, total_mass);
                    merged[i] = merged[j] = true;
                    did_merge = true;
                    break;
                }
            }

            if (!did_merge && !merged[i]) {
                new_particles.push_back(pi);
            }
        }

        particles = std::move(new_particles);
    }

    void step(double dt) {
        compute_gravitational_forces();
        for (auto& p : particles) {
            p.update(dt);
        }
        handle_collisions();
        time += dt;
    }

    void log_state() {
        std::cout << "\nTime: " << std::fixed << std::setprecision(2) << time 
                  << "s | Particle count: " << particles.size() << std::endl;
        for (const auto& p : particles) {
            std::cout << p << std::endl;
        }
    }
};

int main() {
    Simulation sim(100);
    int steps = 1000;
    double dt = 1.0;

    for (int i = 0; i < steps; ++i) {
        sim.step(dt);
        if (static_cast<int>(sim.time) % 10 == 0) {
            sim.log_state();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    return 0;
} 