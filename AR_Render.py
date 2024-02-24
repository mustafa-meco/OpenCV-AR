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
import pygame


from tools.Visualize import draw_axis
from objloader import * #Load obj and corresponding material and textures.
from MatrixTransform import extrinsic2ModelView, intrinsic2Project 
from Filter import Filter
from tools.Aruco_Modular import *
from Board import get_object_by_id

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
        glPointSize(3)  # Change the number to adjust the size
        glBegin(GL_POINTS)
        glVertex3fv(self.position)
        glEnd()

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_particle(self, position, velocity, color):
        lifespan = random.uniform(3.0, 10.0)
        particle = Particle(position, velocity, color, lifespan)
        self.particles.append(particle)

    def update(self, dt):
        for particle in self.particles:
            particle.update(dt)

        self.particles = [p for p in self.particles if p.lifespan > 0.0]

    def draw(self):
        for particle in self.particles:
            particle.draw()

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
        # self.welding_particle_system = ParticleSystem()
        # # self.fire_particle_system = FireParticleSystem()
        # # self.colliding_objects = []  # List to store colliding objects
        # # self.dt = 10.0
        self.particle_system = ParticleSystem()
        pygame.mixer.init()
        pygame.mixer.music.load("welding.wav")
        
        self.filter = Filter() # filter for extrinsic matrix.        

    def loadModel(self, model_name):
        # self.models[model_name]={"object": OBJ(f"{self.objects_path}/{model_name}/{model_name.lower()}.obj", swapyz=True),
        #                     "pre_extrinsicMatrix":None ,
        #                     "rvecs": None,
        #                     "tvecs": None,
        #                     "extrinsicMatrix": None,
        #                     "board": None}
        return OBJ(f"{self.objects_path}/{model_name}/{model_name.lower()}.obj", swapyz=model_name not in ["Cuboid"])
    
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
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.particle_system.update(0.1)
        self.particle_system.draw()
        glColor3f(1.0, 1.0, 1.0)  # Reset color to white
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
                    if board_name_1 != board_name_2 and board_1["detected"] and board_2["detected"]:  # Avoid self-collision checks
                        collision_status = self.check_collision(board_1, board_2)
                        if collision_status[0] and collision_status[1] and collision_status[2]:
                            self.handle_collision(board_name_1, board_name_2)
                                                
        cv2.imshow("Frame",image)
        cv2.waitKey(10)

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
            collision_x = abs(pos1[0] - pos2[0]) * 1.5  < (size1[0] + size2[0]) + tolerance
            collision_y = abs(pos1[1] - pos2[1]) * 1.5  < (size1[1] + size2[1]) + tolerance
            collision_z = abs(pos1[2] - pos2[2])  *1.5  < (size1[2] + size2[2]) + tolerance
            # print(collision_x, collision_y, collision_z)
            # print(distance)
            # If there is a collision along all axes, the boards intersect
            return (collision_x , collision_y , collision_z)
        except:
            return (False, False, False)

    def handle_collision(self, board_name_1, board_name_2):
        glColor3f(1.0, 0.0, 0.0)  # Red color for the collision effect
        draw_text(10, 10, "Collision Detected!",scale=1.5)  # Display collision text
        glColor3f(1.0, 1.0, 1.0)  # Reset color to white
        pos1 = np.array(self.boards[board_name_1]["tvecs"][:, 0])
        size1 = np.array(self.boards[board_name_1]["dimension"])

        pos2 = np.array(self.boards[board_name_2]["tvecs"][:, 0])
        size2 = np.array(self.boards[board_name_2]["dimension"])
        # get point at the center of the two boards
        point = (pos1 + pos2) / 2
        vel = [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0.1, 0.5)]
        color = [random.uniform(0.5, 1.0), random.uniform(0.0, 0.5), 0.0]
        self.particle_system.emit_particle(point, vel, color)
        # play sound of welding
        
        pygame.mixer.music.play()

        # self.particle_system.update(0.1)
        # self.particle_system.draw()
        
        # # print(f"Collision detected between {board_name_1} and {board_name_2}")
        # # Create a new welding spark particle system
        # self.welding_particle_system.emitter_position = self.boards[board_name_1]["tvecs"]
        # # Create a new fire particle system
        # self.fire_particle_system.emitter_position = self.boards[board_name_1]["tvecs"]
        # # Update the particle systems
        # self.welding_particle_system.update(self.dt)
        # self.fire_particle_system.update(self.dt)
        # # Draw the particle systems
        # self.welding_particle_system.draw()
        # self.fire_particle_system.draw()

    def run(self):
        # Begin to render
        glutMainLoop()

if __name__ == "__main__":
    # The value of cam_matrix and dist_coeff from your calibration by using chessboard.
    cam_matrix, dist_coeff, r_vectors, t_vectors = load_calib_data('./calib_data\MultiMatrixMobile.npz')

    ar_instance = AR_render("https://192.168.1.2:4343/video", cam_matrix, dist_coeff)
    ar_instance.run()