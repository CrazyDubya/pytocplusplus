import math
import random
import time

G = 6.67430e-11  # Gravitational constant

class Vector2D:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Vector2D(self.x / scalar, self.y / scalar)

    def magnitude(self):
        return math.hypot(self.x, self.y)

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector2D()
        return self / mag

    def distance_to(self, other):
        return (self - other).magnitude()

    def __repr__(self):
        return f"({self.x:.2e}, {self.y:.2e})"

class Particle:
    def __init__(self, id, position, velocity, mass):
        self.id = id
        self.position = position
        self.velocity = velocity
        self.mass = mass
        self.force = Vector2D()

    def apply_force(self, f):
        self.force = self.force + f

    def update(self, dt):
        acceleration = self.force / self.mass
        self.velocity = self.velocity + acceleration * dt
        self.position = self.position + self.velocity * dt
        self.force = Vector2D()  # reset force

    def __repr__(self):
        return f"[#{self.id} m={self.mass:.2e} pos={self.position} vel={self.velocity}]"

class Simulation:
    def __init__(self, num_particles, bounds=1e9):
        self.particles = []
        self.time = 0.0
        self.bounds = bounds
        for i in range(num_particles):
            position = Vector2D(
                random.uniform(-bounds, bounds),
                random.uniform(-bounds, bounds)
            )
            velocity = Vector2D(
                random.uniform(-1000, 1000),
                random.uniform(-1000, 1000)
            )
            mass = random.uniform(1e20, 1e24)
            self.particles.append(Particle(i, position, velocity, mass))

    def compute_gravitational_forces(self):
        n = len(self.particles)
        for i in range(n):
            for j in range(i + 1, n):
                pi = self.particles[i]
                pj = self.particles[j]
                displacement = pj.position - pi.position
                distance = displacement.magnitude() + 1e-5  # Avoid div-by-zero
                force_magnitude = G * pi.mass * pj.mass / (distance ** 2)
                force_dir = displacement.normalize()
                force = force_dir * force_magnitude
                pi.apply_force(force)
                pj.apply_force(force * -1)

    def handle_collisions(self, merge_distance=1e6):
        merged = set()
        n = len(self.particles)
        new_particles = []

        for i in range(n):
            if i in merged:
                continue
            pi = self.particles[i]
            for j in range(i + 1, n):
                if j in merged:
                    continue
                pj = self.particles[j]
                if pi.position.distance_to(pj.position) < merge_distance:
                    # Merge particles
                    total_mass = pi.mass + pj.mass
                    new_pos = (pi.position * pi.mass + pj.position * pj.mass) / total_mass
                    new_vel = (pi.velocity * pi.mass + pj.velocity * pj.mass) / total_mass
                    new_particles.append(Particle(
                        pi.id, new_pos, new_vel, total_mass
                    ))
                    merged.add(i)
                    merged.add(j)
                    break
            else:
                if i not in merged:
                    new_particles.append(pi)

        self.particles = new_particles

    def step(self, dt):
        self.compute_gravitational_forces()
        for p in self.particles:
            p.update(dt)
        self.handle_collisions()
        self.time += dt

    def log_state(self):
        print(f"\nTime: {self.time:.2f}s | Particle count: {len(self.particles)}")
        for p in self.particles:
            print(p)

def main():
    sim = Simulation(num_particles=100)
    steps = 1000
    dt = 1.0

    for _ in range(steps):
        sim.step(dt)
        if int(sim.time) % 10 == 0:
            sim.log_state()
        time.sleep(0.01)  # To simulate real-time output, remove for benchmarking

if __name__ == "__main__":
    main()