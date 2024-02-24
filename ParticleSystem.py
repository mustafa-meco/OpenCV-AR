import random
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import glm

import numpy as np

class Particle:
    def __init__(self, position, velocity, age, life_span):
        self.position = position
        self.velocity = velocity
        self.age = age
        self.life_span = life_span


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.emitter_position = np.zeros(3)  # Use numpy array instead of glm.vec3
        self.spawn_rate = 10
        self.spawn_age = 2

    def update(self, dt):
        self.spawn_age += dt
        if self.spawn_age > 1 / self.spawn_rate:
            self.spawn_age -= 1 / self.spawn_rate
            new_particle_position = self.emitter_position.copy()
            new_particle_velocity = np.random.uniform(
                low=-0.1, high=0.1, size=(3,))  # Generate random velocity
            new_particle_age = 0
            new_particle_life_span = np.random.uniform(
                low=0.5, high=1.5)  # Generate random lifespan
            new_particle = Particle(new_particle_position, new_particle_velocity, new_particle_age, new_particle_life_span)
            self.particles.append(new_particle)

        for particle in self.particles:
            particle.age += dt
            if particle.age > particle.life_span:
                self.particles.remove(particle)
                continue
            particle.position += particle.velocity * dt

    def draw(self):
        glBegin(GL_POINTS)
        for particle in self.particles:
            glColor3f(1, 0.5, 0)  # Welding spark color
            glVertex3f(*particle.position)
        glEnd()


class FireParticle:
    def __init__(self, position, velocity, age, life_span, color):
        self.position = np.array(position, dtype=np.float32)  # Use numpy array instead of glm.vec3
        self.velocity = np.array(velocity, dtype=np.float32)  # Use numpy array instead of glm.vec3
        self.age = age
        self.life_span = life_span
        self.color = color

class FireParticleSystem:
    def __init__(self):
        self.particles = []
        self.emitter_position = np.zeros(3)  # Use numpy array instead of glm.vec3
        self.spawn_rate = 10
        self.spawn_age = 2

    def update(self, dt):
        self.spawn_age += dt
        if self.spawn_age > 1 / self.spawn_rate:
            self.spawn_age -= 1 / self.spawn_rate
            new_particle_position = self.emitter_position.copy()
            new_particle_velocity = np.random.uniform(
                low=-0.1, high=0.1, size=(3,))  # Generate random velocity
            new_particle_age = 0
            new_particle_life_span = np.random.uniform(
                low=0.5, high=1.5)  # Generate random lifespan
            new_particle_color = (np.random.uniform(low=0.6, high=1.0),
                                  np.random.uniform(low=0.2, high=0.5),
                                  0)  # Generate random color
            new_particle = FireParticle(new_particle_position, new_particle_velocity, new_particle_age, new_particle_life_span, new_particle_color)
            self.particles.append(new_particle)

        for particle in self.particles:
            particle.age += dt
            if particle.age > particle.life_span:
                self.particles.remove(particle)
                continue
            particle.position += particle.velocity * dt

    def draw(self):
        glBegin(GL_POINTS)
        for particle in self.particles:
            glColor3f(*particle.color)  # Fire color
            glVertex3f(*particle.position)
        glEnd()