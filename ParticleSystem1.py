from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pygame
import numpy as np
import random

class Particle:
    def __init__(self, position, velocity, color, lifespan):
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)
        self.color = color
        self.lifespan = lifespan

    def update(self, dt):
        self.position += self.velocity * dt
        self.lifespan -= dt

    def draw(self):
        glColor3f(*self.color)
        glPointSize(2)  # Change the number to adjust the size
        glBegin(GL_POINTS)  # Change this line
        glVertex3fv(self.position)
        glEnd()


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_particle(self):
        position = [0.0, 0.0, 0.0]
        velocity = [random.uniform(-0.1, 0.1), random.uniform(0.1, 0.5), random.uniform(-0.1, 0.1)]
        color = [random.uniform(0.5, 1.0), random.uniform(0.0, 0.5), 0.0]  
        lifespan = random.uniform(1.0, 3.0)
        particle = Particle(position, velocity, color, lifespan)
        self.particles.append(particle)

    def update(self, dt):
        for particle in self.particles:
            particle.update(dt)

        self.particles = [p for p in self.particles if p.lifespan > 0.0]

    def draw(self):
        for particle in self.particles:
            particle.draw()

particle_system = ParticleSystem()

def draw_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    particle_system.update(0.1)
    particle_system.draw()

    glutSwapBuffers()

def idle():
    particle_system.emit_particle()
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b'Particle System Example')
    
    glutDisplayFunc(draw_scene)
    glutIdleFunc(idle)
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 1, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(0, 5, 5, 0, 0, 0, 0, 1, 0)

    glutMainLoop()

if __name__ == "__main__":
    main()
