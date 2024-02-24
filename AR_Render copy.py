from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import cv2
import cv2.aruco as aruco
from PIL import Image
import numpy as np
import imutils
import sys
import os
import glm
import random

from tools.Visualize import draw_axis
from objloader import * #Load obj and corresponding material and textures.
from MatrixTransform import extrinsic2ModelView, intrinsic2Project 
from Filter import Filter
from tools.Aruco_Modular import *
from Board import get_object_by_id
import numpy as np


class Particle:
    def __init__(self, position, velocity, lifetime):
        self.position = position
        self.velocity = velocity
        self.lifetime = lifetime

    def update(self, delta_time):
        self.position += self.velocity * delta_time
        self.lifetime -= delta_time

    def is_alive(self):
        return self.lifetime > 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_spark(self, position, intensity):
        # Emit a spark particle at the given position with a random velocity and lifetime
        velocity = glm.vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1)) * intensity
        lifetime = np.random.uniform(0.5, 1.5)
        self.particles.append(Particle(position, velocity, lifetime))

    def update_particles(self, delta_time):
        # Update particle positions and lifetimes
        for particle in self.particles:
            particle.update(delta_time)
        # Remove dead particles
        self.particles = [particle for particle in self.particles if particle.is_alive()]

    def render_particles(self):
        # Render particles as points or textured quads
        glBegin(GL_POINTS)
        for particle in self.particles:
            # Render each particle as a point with additive blending
            glColor4f(1.0, 1.0, 1.0, particle.lifetime)  # Adjust alpha based on particle lifetime
            glVertex3f(*particle.position)
        glEnd()

class FireParticle:
    def __init__(self, position, velocity, color, size, lifetime):
        self.position = position
        self.velocity = velocity
        self.color = color
        self.size = size
        self.lifetime = lifetime

    def update(self, delta_time):
        self.position += self.velocity * delta_time
        self.lifetime -= delta_time

    def is_alive(self):
        return self.lifetime > 0


class FireParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_fire_particle(self, position, intensity):
        # Spawn a fire particle at the given position with a random velocity and lifetime
        velocity = glm.vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1)) * intensity
        color = (1.0, np.random.uniform(0.5, 1.0), 0.0)  # Randomize color within range
        size = np.random.uniform(0.05, 0.1)  # Randomize size within range
        lifetime = np.random.uniform(1.0, 2.0)
        self.particles.append(FireParticle(position, velocity, color, size, lifetime))

    def update_particles(self, delta_time):
        # Update particle positions and lifetimes
        for particle in self.particles:
            particle.update(delta_time)
        # Remove dead particles
        self.particles = [particle for particle in self.particles if particle.is_alive()]

    def render_particles(self):
        # Render particles as textured quads
        for particle in self.particles:
            # Render each particle as a textured quad
            glColor3f(*particle.color)
            glBegin(GL_QUADS)
            glVertex3f(particle.position[0] - particle.size / 2, particle.position[1] - particle.size / 2, particle.position[2])
            glVertex3f(particle.position[0] + particle.size / 2, particle.position[1] - particle.size / 2, particle.position[2])
            glVertex3f(particle.position[0] + particle.size / 2, particle.position[1] + particle.size / 2, particle.position[2])
            glVertex3f(particle.position[0] - particle.size / 2, particle.position[1] + particle.size / 2, particle.position[2])
            glEnd()

def draw_text(x, y, text):
    glWindowPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(character))

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, scale=1.0):
    glWindowPos2f(x, y)
    for character in text:
        glutBitmapCharacter(font, ord(character))
        glTranslatef(scale, 0, 0)  # Increase x-coordinate to scale text


class AR_render:

    def __init__(self, camera_url, camera_matrix, dist_coefs, objects_path="Models", model_scale=0.03):
        
        self.cam = cv2.VideoCapture(camera_url)
        self.image_w, self.image_h = map(int, (self.cam.get(3), self.cam.get(4)))
        self.initOpengl(self.image_w, self.image_h)
        self.objects_path = objects_path
        self.model_scale = model_scale

        self.cam_matrix, self.dist_coefs = camera_matrix, dist_coefs
        self.projectMatrix = intrinsic2Project(self.cam_matrix, self.image_w, self.image_h, 0.01, 100.0)
        self.boards = {}
        self.init_boards()
        # models = ["Cube", "Cuboid"]
        # for model in models:
        #     self.loadModel(model)
        self.welding_particle_system = ParticleSystem()
        self.fire_particle_system = FireParticleSystem()
        self.colliding_objects = []  # List to store colliding objects

        
        self.filter = Filter() # filter for extrinsic matrix.
        

    def loadModel(self, model_name):
        # self.models[model_name]={"object": OBJ(f"{self.objects_path}/{model_name}/{model_name.lower()}.obj", swapyz=True),
        #                     "pre_extrinsicMatrix":None ,
        #                     "rvecs": None,
        #                     "tvecs": None,
        #                     "extrinsicMatrix": None,
        #                     "board": None}
        return OBJ(f"{self.objects_path}/{model_name}/{model_name.lower()}.obj", swapyz=model_name not in ["Cuboid"])
    
    # def getBoardFromId(self, id, marker_size, margin):
    #     corners, ids, name = get_object_by_id(id, marker_size, margin)
    #     if name == "Cube":
    #         self.loadModel("Cube")
    #     else:
    #         return None, None
    #     return corners, ids
    
    def init_boards(self, boards_details_path="Boards_details"):
        # Specify the path to the directory containing Boards_details
        directory_path = boards_details_path

        # Get the names of the directories in Boards_details
        board_names = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
        
        self.aruco_dict, self.parameters=setup_detector()
        self.parameters.adaptiveThreshConstant = 10

        for board_name in board_names:
            # Get the path to the directory containing the board data
            board_path = os.path.join(directory_path, board_name)

            # Get the path to the corners.npy file
            corners_path = os.path.join(board_path, "board_corners.npy")

            # Get the path to the ids.npy file
            ids_path = os.path.join(board_path, "board_ids.npy")

            # Read the corners.npy file
            corners = np.load(corners_path)

            # Read the ids.npy file
            ids = np.load(ids_path)

            
            self.boards[board_name] = {"board": aruco.Board(corners, self.aruco_dict, ids),
                                       "pre_extrinsicMatrix":None,
                                        "detected": False }
            
                
            if board_name == "Cube2x2":
                self.boards[board_name]["object"] = self.loadModel("Cube")
                self.boards[board_name]["dimension"] = (0.05, 0.05, 0.05)
                self.boards[board_name]["scale"] = 0.06
            elif board_name == "Cube34":
                self.boards[board_name]["object"] = self.loadModel("Cube2")
                self.boards[board_name]["dimension"] = (0.034, 0.034, 0.034)
                self.boards[board_name]["scale"] = 0.04
            elif board_name == "Cuboid":
                self.boards[board_name]["object"] = self.loadModel("Cuboid")
                self.boards[board_name]["scale"] = 0.01
            elif board_name == "Cylinder":
                self.boards[board_name]["object"] = self.loadModel("Cylinder")
                self.boards[board_name]["scale"] = 0.0005
        
    
    def initOpengl(self, width, height, pos_x = 500, pos_y = 500, window_name = b'Aruco Demo'):
        
        """[Init opengl configuration]
        
        Arguments:
            width {[int]} -- [width of opengl viewport]
            height {[int]} -- [height of opengl viewport]
        
        Keyword Arguments:
            pos_x {int} -- [X cordinate of viewport] (default: {500})
            pos_y {int} -- [Y cordinate of viewport] (default: {500})
            window_name {bytes} -- [Window name] (default: {b'Aruco Demo'})
        """
        
        glutInit()
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(width, height)
        glutInitWindowPosition(pos_x, pos_y)
     
        
        
        
        self.window_id = glutCreateWindow(window_name)
        glutDisplayFunc(self.draw_scene)
        glutIdleFunc(self.draw_scene)
        
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glShadeModel(GL_SMOOTH)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        
        # # Assign texture
        glEnable(GL_TEXTURE_2D)
        
        # # Add listener
        # glutKeyboardFunc(self.keyBoardListener)
        
        # Set ambient lighting
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5,0.5,0.5,1)) 
          
    def draw_scene(self):
        """[Opengl render loop]
        """
        _, image = self.cam.read()# get image from cam camera.
        self.draw_background(image)  # draw background
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_objects(image)
        glutSwapBuffers()
    
    def draw_background(self, image):
        """[Draw the background and tranform to opengl format]
        
        Arguments:
            image {[np.array]} -- [frame from your camera]
        """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Setting background image project_matrix and model_matrix.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(33.7, 1.3, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
     
        # Convert image to OpenGL texture format
        bg_image = cv2.flip(image, 0)
        bg_image = Image.fromarray(bg_image)     
        ix = bg_image.size[0]
        iy = bg_image.size[1]
        bg_image = bg_image.tobytes("raw", "BGRX", 0, -1)
  
  
        # Create background texture
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, bg_image)
                
        glTranslatef(0.0,0.0,-10.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3f(-4.0, -3.0, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( 4.0, -3.0, 0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( 4.0,  3.0, 0.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-4.0,  3.0, 0.0)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)

    def draw_objects(self, image):
        height, width, channels = image.shape

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, self.aruco_dict, parameters = self.parameters)
        for board_name in self.boards.keys():
            self.boards[board_name]["rvecs"], self.boards[board_name]["tvecs"], self.boards[board_name]["model_matrix"] = None, None, None
        if ids is not None and corners is not None:
            for board_name in self.boards.keys():
                self.boards[board_name]["detected"] = False
                new_ids, new_corners = self.filter.ids_corners_by_object(ids, corners, self.boards[board_name]["board"].getIds())
                if len(new_ids) > 0 and len(new_corners) > 0:
                    self.boards[board_name]["detected"] = True
                    _, self.boards[board_name]["rvecs"], self.boards[board_name]["tvecs"] = cv2.aruco.estimatePoseBoard(new_corners, new_ids, self.boards[board_name]["board"], self.cam_matrix, self.dist_coefs, self.boards[board_name]["rvecs"], self.boards[board_name]["tvecs"])        
                    # if self.boards[board_name]["rvecs"].shape[0] > 3:
                    #     self.boards[board_name]["rvecs"] = self.boards[board_name]["rvecs"][0]
                    #     self.boards[board_name]["tvecs"] = self.boards[board_name]["tvecs"]

                    new_rvecs = self.boards[board_name]["rvecs"]
                    new_tvecs = self.boards[board_name]["tvecs"]
                    try:
                        test = draw_axis(image, new_rvecs, new_tvecs, self.cam_matrix, self.dist_coefs)
                    except:
                        pass
        
        projectMatrix = intrinsic2Project(self.cam_matrix, width, height, 0.01, 100.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(projectMatrix)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        

        for board_name in self.boards.keys():
            if self.boards[board_name]["tvecs"] is not None:
                self.boards[board_name]["model_matrix"] = extrinsic2ModelView(self.boards[board_name]["rvecs"], self.boards[board_name]["tvecs"])
                
                # if self.filter.update_board(self.boards[board_name]["tvecs"]): # the mark is moving
                #     self.boards[board_name]["model_matrix"] = extrinsic2ModelView(self.boards[board_name]["rvecs"], self.boards[board_name]["tvecs"])
                # else:
                #     self.boards[board_name]["model_matrix"] = self.boards[board_name]["pre_extrinsicMatrix"]
            else:
                # self.boards[board_name]["model_matrix"] = self.boards[board_name]["pre_extrinsicMatrix"]
                self.boards[board_name]["model_matrix"] = None
                
            if self.boards[board_name]["model_matrix"] is not None:
                self.boards[board_name]["pre_extrinsicMatrix"] = self.boards[board_name]["model_matrix"]
                glLoadMatrixf(self.boards[board_name]["model_matrix"])
                glScaled(self.boards[board_name]["scale"], self.boards[board_name]["scale"], self.boards[board_name]["scale"])
                glTranslatef(0, 0, 0)
                glCallList(self.boards[board_name]["object"].gl_list)
        
        for board_name_1, board_1 in self.boards.items():
            for board_name_2, board_2 in self.boards.items():
                if board_name_1 != board_name_2 and board_1["detected"] and board_2["detected"]:
                    self.handle_collision(board_1, board_2)

        
        cv2.imshow("Frame",image)
        cv2.waitKey(20)

    def check_collision(self, board1, board2):
        try:
            # Extract relevant information from the boards
            pos1 = np.array(board1["tvecs"][:, 0])
            size1 = np.array(board1["dimension"])

            pos2 = np.array(board2["tvecs"][:, 0])
            size2 = np.array(board2["dimension"])

            distance = np.linalg.norm(pos1 - pos2)
            tolerance = 0.01
            # Check for collision along each axis
            collision_x = abs(pos1[0] - pos2[0]) * 2 < (size1[0] + size2[0]) + tolerance
            collision_y = abs(pos1[1] - pos2[1]) * 2 < (size1[1] + size2[1]) + tolerance
            collision_z = abs(pos1[2] - pos2[2]) * 2 < (size1[2] + size2[2]) + tolerance
            # print(collision_x, collision_y, collision_z)
            # print(distance)
            # If there is a collision along all axes, the boards intersect
            return collision_x and collision_y and collision_z
        except:
            return False
        
    def handle_collision(self, board1, board2):
        if self.check_collision(board1, board2):
            glColor3f(1.0, 0.0, 0.0)  # Red color for the collision effect
            draw_text(10, 10, "Collision Detected!",scale=1.5)  # Display collision text
            

            glColor3f(1.0, 1.0, 1.0)  # Reset color to white
            
            # Trigger welding effect
            self.trigger_welding_effect(board1, board2)

            # Add fire effect
            self.add_fire_effect(board1, board2)

    def trigger_welding_effect(self, board1, board2):
        # change color to yellow
        glColor3f(1.0, 1.0, 0.0)  # Yellow color for welding effect

        # change the color temporarily
        glPushMatrix()
        glLoadMatrixf(board1["model_matrix"])
        glScaled(board1["scale"], board1["scale"], board1["scale"])
        glTranslatef(0, 0, 0)
        glCallList(board1["object"].gl_list)
        glPopMatrix()

        glPushMatrix()
        glLoadMatrixf(board2["model_matrix"])
        glScaled(board2["scale"], board2["scale"], board2["scale"])
        glTranslatef(0, 0, 0)
        glCallList(board2["object"].gl_list)
        glPopMatrix()

        # Reset color to white
        glColor3f(1.0, 1.0, 1.0)

    def add_fire_effect(self, board1, board2):
        # Calculate the position of the fire effect between the two colliding objects
        fire_position = (
            (board1["tvecs"][0][0] + board2["tvecs"][0][0]) / 2,  # Average of x positions
            (board1["tvecs"][1][0] + board2["tvecs"][1][0]) / 2,  # Average of y positions
            (board1["tvecs"][2][0] + board2["tvecs"][2][0]) / 2   # Average of z positions
        )

        # Calculate the size of the fire effect based on the distance between the two objects
        distance = np.linalg.norm(np.array(board1["tvecs"][:, 0]) - np.array(board2["tvecs"][:, 0]))
        fire_size = distance / 10.0  # Adjust this scaling factor as needed

        # Render the fire effect between the colliding objects
        for _ in range(50):  # Render 50 fire particles
            glPushMatrix()

            # Randomly displace each fire particle around the collision point
            displacement = (
                random.uniform(-fire_size, fire_size),
                random.uniform(-fire_size, fire_size),
                random.uniform(-fire_size, fire_size)
            )
            particle_position = (
                fire_position[0] + displacement[0],
                fire_position[1] + displacement[1],
                fire_position[2] + displacement[2]
            )

            # Set the color of the fire particle (e.g., shades of orange and yellow)
            glColor3f(1.0, random.uniform(0.1, 0.5), 0.0)  # Vary the green component for color variation
            glPointSize(3.0)  # Set the size of the fire particles
            glBegin(GL_POINTS)
            glVertex3f(*particle_position)  # Render fire particle at the calculated position
            glEnd()

            glPopMatrix()
        
    def accurate_check_collision(self, board1, board2):
        try:
            # Extract relevant information from the boards
            pos1 = np.array(board1["tvecs"][:, 0])
            size1 = np.array(board1["dimension"])

            pos2 = np.array(board2["tvecs"][:, 0])
            size2 = np.array(board2["dimension"])

            # Calculate the center points of the boards
            center1 = pos1 + size1 / 2
            center2 = pos2 + size2 / 2

            # Calculate the direction vector of the raycast
            direction = center2 - center1
            direction /= np.linalg.norm(direction)

            # Calculate the distance between the centers of the boards
            distance = np.linalg.norm(center2 - center1)

            # Perform the raycast
            for t in np.linspace(0, distance, num=100):
                point = center1 + t * direction

                # Check if the point is within the bounds of both boards
                within_bounds1 = np.all(np.abs(point - center1)*0.9 <= size1 / 2)
                within_bounds2 = np.all(np.abs(point - center2)*0.9 <= size2 / 2)

                if within_bounds1 and within_bounds2:
                    # Collision detected
                    return True

            # No collision detected
            return False
        except:
            return False
    
    def raycast_collision(self , board1, board2):
        try:
            # Extract relevant information from the boards
            pos1 = np.array(board1["tvecs"][:, 0])
            size1 = np.array(board1["dimension"])

            pos2 = np.array(board2["tvecs"][:, 0])
            size2 = np.array(board2["dimension"])

            # Calculate the center points of the boards
            center1 = pos1 + size1 / 2
            center2 = pos2 + size2 / 2

            # Calculate the direction vector of the raycast
            direction = center2 - center1
            direction /= np.linalg.norm(direction)

            # Calculate the distance between the centers of the boards
            distance = np.linalg.norm(center2 - center1)

            # Perform the raycast
            for t in np.linspace(0, distance, num=100):
                point = center1 + t * direction

                # Check if the point is within the bounds of both boards
                within_bounds1 = np.all(np.abs(point - center1) <= size1 / 2)
                within_bounds2 = np.all(np.abs(point - center2) <= size2 / 2)

                if within_bounds1 and within_bounds2:
                    # Collision detected
                    return True

            # No collision detected
            return False
        except:
            return False
    
    # def check_collision(self, board1, board2, threshold_distance=0.1):
    #     try: 
    #         # Assuming the third column of rvecs is the forward direction
    #         board1_direction = board1["rvecs"][:, 2]
    #         board1_origin = board1["tvecs"][:, 0]

    #         intersection_point = self.ray_intersect(board1_origin, board1_direction, board2)
    #         if intersection_point is not None:
    #             distance = glm.distance(glm.vec3(board1_origin), glm.vec3(intersection_point))
    #             print(f" Distance: {distance}")
    #             if distance < threshold_distance:
    #                 print(f"Collision")
    #                 return True

    #         return False
    #     except:
    #         return False

    # def ray_intersect(self, board_origin, board_direction, target_board):
    #     # Ray-plane intersection between the ray and the target board
    #     normal = glm.cross(target_board["rvecs"][:, 2], target_board["rvecs"][:, 0])  # Assuming the third column of rvecs is the forward direction
    #     d = -glm.dot(target_board["tvecs"][:, 0], normal)
        
    #     denom = glm.dot(board_direction, normal)
    #     if abs(denom) > 1e-6:
    #         t = -(glm.dot(board_origin, normal) + d) / denom
    #         if t >= 0:
    #             intersection_point = board_origin + t * board_direction
    #             return intersection_point

    #     return None
        
    # def handle_collision(self, collision_point, collision_intensity):
    #     # Spawn welding particles at the collision point with the given intensity
    #     for _ in range(100):
    #         self.welding_particle_system.emit_spark(collision_point, collision_intensity)
    #     # Spawn fire particles at the collision point with the given intensity
    #     for _ in range(50):
    #         self.fire_particle_system.spawn_fire_particle(collision_point, collision_intensity)

    def update(self, delta_time):
        # Update particle systems
        self.welding_particle_system.update_particles(delta_time)
        self.fire_particle_system.update_particles(delta_time)

    def render(self):
        # Render colliding objects
        self.render_colliding_objects()

        # Enable alpha blending for particles
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Render welding particles
        self.welding_particle_system.render_particles()

        # Render fire particles
        self.fire_particle_system.render_particles()

        # Disable alpha blending
        glDisable(GL_BLEND)
    
    def render_colliding_objects(self):
        # Render colliding objects
        for obj in self.colliding_objects:
            # Render each object using OpenGL
            pass  # Add your object rendering code here
    


    def run(self):
        # Begin to render
        glutMainLoop()




if __name__ == "__main__":
    # The value of cam_matrix and dist_coeff from your calibration by using chessboard.
    cam_matrix, dist_coeff, r_vectors, t_vectors = load_calib_data('./calib_data\MultiMatrixMobile.npz')

    ar_instance = AR_render('https://192.168.1.2:4343/video', cam_matrix, dist_coeff)
    ar_instance.run()     
    