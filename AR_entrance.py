from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import cv2
import cv2.aruco as aruco
from PIL import Image
import numpy as np
import imutils
import sys

 
from tools.Visualize import draw_axis
from objloader import * #Load obj and corresponding material and textures.
from MatrixTransform import extrinsic2ModelView, intrinsic2Project 
from Filter import Filter
from tools.Aruco_Modular import *
from Board import get_object_by_id


class AR_render:
    
    def __init__(self, camera_url, camera_matrix, dist_coefs, rvecs, tvecs, object_path, model_scale = 0.03):
        
        """[Initialize]
        
        Arguments:
            camera_matrix {[np.array]} -- [your camera intrinsic matrix]
            dist_coefs {[np.array]} -- [your camera difference parameters]
            object_path {[string]} -- [your model path]
            model_scale {[float]} -- [your model scale size]
        """
        # Initialise webcam and start thread
        # self.webcam = cv2.VideoCapture(0)
        self.webcam = cv2.VideoCapture(camera_url) # 0 for webcam, 1 for external camera  # TODO add camera selection
        self.image_w, self.image_h = map(int, (self.webcam.get(3), self.webcam.get(4))) # get image size from camera configuration.    
        self.initOpengl(self.image_w, self.image_h) # init opengl configuration and viewport size is the same as image size.       
        self.model_scale = model_scale # model scale size that you can adjust by key board '+' and '-'    
    
        self.cam_matrix,self.dist_coefs = camera_matrix, dist_coefs # camera matrix and difference parameters from your calibration.   
        self.rvecs, self.tvecs = rvecs, tvecs # rotation vectors and translation vectors from your calibration.
        self.projectMatrix = intrinsic2Project(camera_matrix, self.image_w, self.image_h, 0.01, 100.0) # project matrix from your camera configuration.   
        self.loadModel(object_path) # load model from object_path   
        
        # Model translate that you can adjust by key board 'w', 's', 'a', 'd'  
        self.translate_x, self.translate_y, self.translate_z = 0, 0, 0
        self.pre_extrinsicMatrix = None # previous extrinsic matrix for filter. 
        
        self.filter = Filter() # filter for extrinsic matrix.
        

    def loadModel(self, object_path):
        
        """[loadModel from object_path]
        
        Arguments:
            object_path {[string]} -- [path of model]
        """
        self.model = OBJ(object_path, swapyz = True) # load model from object_path and swapyz = True for opengl coordinate system. 

  
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
        
        # Add listener
        glutKeyboardFunc(self.keyBoardListener)
        
        # Set ambient lighting
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5,0.5,0.5,1)) 
        
        
        
        
 
    def draw_scene(self):
        """[Opengl render loop]
        """
        _, image = self.webcam.read()# get image from webcam camera.
        self.draw_background(image)  # draw background
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # self.draw_objects_1Marker(image, mark_size = 0.06) # draw the 3D objects.
        # self.draw_objects_GridBoard(image, mark_size = 0.06, mark_sep = 0.0045)
        self.draw_objects_Board(image, mark_size = 0.034, mark_margin=0.001)
        glutSwapBuffers()
    
        
        # TODO add close button
        # key = cv2.waitKey(20)
        
       
        
 
 
 
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
 
 
 
    def draw_objects_1Marker(self, image, mark_size = 0.0375):
        """[draw models with opengl]
        
        Arguments:
            image {[np.array]} -- [frame from your camera]
        
        Keyword Arguments:
            mark_size {float} -- [aruco mark size: unit is meter] (default: {0.07})
        """
        # aruco data
        # aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)      
        key = getattr(aruco, f'DICT_ARUCO_ORIGINAL')
        aruco_dict = aruco.getPredefinedDictionary(key)

        parameters = aruco.DetectorParameters()
        parameters.adaptiveThreshConstant = 10

        height, width, channels = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters = parameters)
        
        rvecs, tvecs, model_matrix = self.rvecs, self.tvecs, None
        
        if ids is not None and corners is not None:
            rvecs, tvecs, _= aruco.estimatePoseSingleMarkers(corners, mark_size , self.cam_matrix, self.dist_coefs)
            new_rvecs = rvecs[0,:,:]
            new_tvecs = tvecs[0,:,:]
            test = draw_axis(image, new_rvecs, new_tvecs, self.cam_matrix, self.dist_coefs)
            # for i in range(rvecs.shape[0]):
            #     aruco.drawAxis(image, self.cam_matrix, self.dist_coefs, rvecs[i, :, :], tvecs[i, :, :], 0.03)
            
        projectMatrix = intrinsic2Project(self.cam_matrix, width, height, 0.01, 100.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(projectMatrix)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
       
        
        if tvecs is not None:
            if self.filter.update(tvecs): # the mark is moving
                model_matrix = extrinsic2ModelView(rvecs, tvecs)
            else:
                model_matrix = self.pre_extrinsicMatrix
        else:
            model_matrix =  self.pre_extrinsicMatrix
        
            
        if model_matrix is not None:     
            self.pre_extrinsicMatrix = model_matrix
            glLoadMatrixf(model_matrix)
            glScaled(self.model_scale, self.model_scale, self.model_scale)
            glTranslatef(self.translate_x, self.translate_y, self.translate_z)
            glCallList(self.model.gl_list)
            
        cv2.imshow("Frame",image)
        cv2.waitKey(20)

    def draw_objects_GridBoard(self, image, mark_size = 0.0375, mark_sep = 0.0045):
        """[draw models with opengl]
        
        Arguments:
            image {[np.array]} -- [frame from your camera]
        
        Keyword Arguments:
            mark_size {float} -- [aruco mark size: unit is meter] (default: {0.07})
        """  

        aruco_dict, parameters=setup_detector()
        parameters.adaptiveThreshConstant = 10

        ids_list = [459,912,646,439,135,266,655,538,473,302,828,1001,64,880,92,431,650,191,1016,919,1014,305,786,180,823,922,35,992,60,407,574,640,850,786,544,56,437,904,299,161,669,844,850,267,372,704,836,480,413,218,662,981,631,661,675,196,147,626,38,878,19,233,881,373,168,500,31,575,267,256,828,950,953,805,661,453,262,392,878,735,749,917,598,74,993,98,292,766,574,966,28,15,197,801,18,871]
        desired_ids = np.array(ids_list[:24])
        board = cv2.aruco.GridBoard((6, 4), mark_size, mark_sep, aruco_dict, desired_ids)

        height, width, channels = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters = parameters)
        
        rvecs, tvecs, model_matrix = self.rvecs, self.tvecs, None
        
        if ids is not None and corners is not None:
            _, rvecs, tvecs = cv2.aruco.estimatePoseBoard(corners, ids, board, self.cam_matrix, self.dist_coefs, rvecs, tvecs)        
            new_rvecs = rvecs[:,:]
            new_tvecs = tvecs[:,:]
            test = draw_axis(image, new_rvecs, new_tvecs, self.cam_matrix, self.dist_coefs)
            # for i in range(rvecs.shape[0]):
            #     aruco.drawAxis(image, self.cam_matrix, self.dist_coefs, rvecs[i, :, :], tvecs[i, :, :], 0.03)
            
        projectMatrix = intrinsic2Project(self.cam_matrix, width, height, 0.01, 100.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(projectMatrix)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
       
        
        if tvecs is not None:
            # print(f"tvecs: {tvecs}")
            if self.filter.update_board(tvecs): # the mark is moving
                model_matrix = extrinsic2ModelView(rvecs, tvecs)
            else:
                model_matrix = self.pre_extrinsicMatrix
        else:
            model_matrix =  self.pre_extrinsicMatrix
        
            
        if model_matrix is not None:     
            self.pre_extrinsicMatrix = model_matrix
            glLoadMatrixf(model_matrix)
            glScaled(self.model_scale, self.model_scale, self.model_scale)
            glTranslatef(self.translate_x, self.translate_y, self.translate_z)
            glCallList(self.model.gl_list)
            
        cv2.imshow("Frame",image)
        cv2.waitKey(20)

    def draw_objects_GridBoard(self, image, mark_size = 0.0375):
        """[draw models with opengl]
        
        Arguments:
            image {[np.array]} -- [frame from your camera]
        
        Keyword Arguments:
            mark_size {float} -- [aruco mark size: unit is meter] (default: {0.07})
        """  

        aruco_dict, parameters=setup_detector()
        parameters.adaptiveThreshConstant = 10

        ids_list = [459,912,646,439,135,266,655,538,473,302,828,1001,64,880,92,431,650,191,1016,919,1014,305,786,180,823,922,35,992,60,407,574,640,850,786,544,56,437,904,299,161,669,844,850,267,372,704,836,480,413,218,662,981,631,661,675,196,147,626,38,878,19,233,881,373,168,500,31,575,267,256,828,950,953,805,661,453,262,392,878,735,749,917,598,74,993,98,292,766,574,966,28,15,197,801,18,871]
        desired_ids = np.array(ids_list[:24])
        board = cv2.aruco.GridBoard((6, 4), mark_size, mark_sep, aruco_dict, desired_ids)

        height, width, channels = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters = parameters)
        
        rvecs, tvecs, model_matrix = self.rvecs, self.tvecs, None
        
        if ids is not None and corners is not None:
            _, rvecs, tvecs = cv2.aruco.estimatePoseBoard(corners, ids, board, self.cam_matrix, self.dist_coefs, rvecs, tvecs)        
            new_rvecs = rvecs[:,:]
            new_tvecs = tvecs[:,:]
            test = draw_axis(image, new_rvecs, new_tvecs, self.cam_matrix, self.dist_coefs)
            # for i in range(rvecs.shape[0]):
            #     aruco.drawAxis(image, self.cam_matrix, self.dist_coefs, rvecs[i, :, :], tvecs[i, :, :], 0.03)
            
        projectMatrix = intrinsic2Project(self.cam_matrix, width, height, 0.01, 100.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(projectMatrix)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
       
        print(f"tvecs: {tvecs.shape}")
        if tvecs is not None:
            if self.filter.update_board(tvecs): # the mark is moving
                model_matrix = extrinsic2ModelView(rvecs, tvecs)
            else:
                model_matrix = self.pre_extrinsicMatrix
        else:
            model_matrix =  self.pre_extrinsicMatrix
        
            
        if model_matrix is not None:     
            self.pre_extrinsicMatrix = model_matrix
            glLoadMatrixf(model_matrix)
            glScaled(self.model_scale, self.model_scale, self.model_scale)
            glTranslatef(self.translate_x, self.translate_y, self.translate_z)
            glCallList(self.model.gl_list)
            
        cv2.imshow("Frame",image)
        cv2.waitKey(20)
    
    def draw_objects_Board(self, image, mark_size = 0.034, mark_margin=0.001):
        """[draw models with opengl]
        
        Arguments:
            image {[np.array]} -- [frame from your camera]
        
        Keyword Arguments:
            mark_size {float} -- [aruco mark size: unit is meter] (default: {0.07})
        """  

        aruco_dict, parameters=setup_detector()
        parameters.adaptiveThreshConstant = 10

        MARGIN = mark_margin
        MARKER_SIZE = mark_size


        p = MARKER_SIZE/2

        # Cube Board
        board_corners = [
            # bottom
            np.array([[p,-p,-p-MARGIN],[p,p,-p-MARGIN],[-p,p,-p-MARGIN],[-p,-p,-p-MARGIN]],dtype=np.float32),
            # top
            np.array([[-p,-p,p+MARGIN],[-p,p,p+MARGIN],[p,p,p+MARGIN],[p,-p,p+MARGIN]],dtype=np.float32),
            # front
            np.array([[p+MARGIN,-p,p],[p+MARGIN,p,p],[p+MARGIN,p,-p],[p+MARGIN,-p,-p]],dtype=np.float32),
            # right
            np.array([[p,p+MARGIN,p],[-p,p+MARGIN,p],[-p,p+MARGIN,-p],[p,p+MARGIN,-p]],dtype=np.float32),
            # back 
            np.array([[-p-MARGIN,p,p],[-p-MARGIN,-p,p],[-p-MARGIN,-p,-p],[-p-MARGIN,p,-p]],dtype=np.float32),
            # left
            np.array([[-p,-p-MARGIN,p],[p,-p-MARGIN,p],[p,-p-MARGIN,-p],[-p,-p-MARGIN,-p]],dtype=np.float32)
        ]
        # 36 mm CUBE
        board_ids = np.array( [[91],[90],[87],[88],[92],[89]], dtype=np.int32)
        

        # boards = dict()

        height, width, channels = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters = parameters)
        # for id in ids:
        #     board_corners, board_ids, board_name = get_object_by_id(id)
        #     boards[board_name] = cv2.aruco.Board(board_corners, aruco_dict, board_ids)

        board = cv2.aruco.Board(board_corners, aruco_dict, board_ids)
        
        rvecs, tvecs, model_matrix = self.rvecs, self.tvecs, None
        
        if ids is not None and corners is not None:
            _, rvecs, tvecs = cv2.aruco.estimatePoseBoard(corners, ids, board, self.cam_matrix, self.dist_coefs, rvecs, tvecs)        
            if rvecs.shape[0] > 3:
                rvecs = rvecs[0]
                tvecs = tvecs[0]

            new_rvecs = rvecs[:,:]
            new_tvecs = tvecs[:,:]
            test = draw_axis(image, new_rvecs, new_tvecs, self.cam_matrix, self.dist_coefs)
            # for i in range(rvecs.shape[0]):
            #     aruco.drawAxis(image, self.cam_matrix, self.dist_coefs, rvecs[i, :, :], tvecs[i, :, :], 0.03)
            
        projectMatrix = intrinsic2Project(self.cam_matrix, width, height, 0.01, 100.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(projectMatrix)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
       
        # model_matrix = extrinsic2ModelView(rvecs, tvecs)

        if tvecs is not None:
            # print(f"tvecs: {tvecs}")
            if self.filter.update_board(tvecs): # the mark is moving
                model_matrix = extrinsic2ModelView(rvecs, tvecs)
            else:
                model_matrix = self.pre_extrinsicMatrix
        else:
            model_matrix =  self.pre_extrinsicMatrix
        
            
        if model_matrix is not None:     
            self.pre_extrinsicMatrix = model_matrix
            glLoadMatrixf(model_matrix)
            glScaled(self.model_scale, self.model_scale, self.model_scale)
            glTranslatef(self.translate_x, self.translate_y, self.translate_z)
            glCallList(self.model.gl_list)
            
        cv2.imshow("Frame",image)
        cv2.waitKey(20)
        

    def keyBoardListener(self, key, x, y):
        """[Use key board to adjust model size and position]
        
        Arguments:
            key {[byte]} -- [key value]
            x {[x cordinate]} -- []
            y {[y cordinate]} -- []
        """
        key = key.decode('utf-8')
        if key == '=':
            self.model_scale += 0.01
        elif key == '-':
            self.model_scale -= 0.01
        elif key == 'w':
            self.translate_x -= 0.01
        elif key == 's':
            self.translate_x += 0.01
        elif key == 'a':
            self.translate_y -= 0.01
        elif key == 'd':
            self.translate_y += 0.01
        elif key == 'z':
            self.translate_z -= 0.01
        elif key == 'x':
            self.translate_z += 0.01
             
        
    def run(self):
        # Begin to render
        glutMainLoop()
  

if __name__ == "__main__":
    def load_calib_data(path):
        """
        Load the calibration data from the .npz file.
        :param path: (str) Path to the .npz file.
        :return: (np.array) Camera matrix.
        :return: (np.array) Distortion coefficients.
        :return: (np.array) Rotation vectors.
        :return: (np.array) Translation vectors.
        """
        calib_data_path = path

        calib_data = np.load(calib_data_path)
        # print(calib_data.files)

        cam_mat = calib_data["camMatrix"]
        dist_coef = calib_data["distCoef"]
        r_vectors = calib_data["rVector"]
        t_vectors = calib_data["tVector"]

        return cam_mat, dist_coef, r_vectors, t_vectors
    # The value of cam_matrix and dist_coeff from your calibration by using chessboard.
    cam_matrix, dist_coeff, r_vectors, t_vectors = load_calib_data('./calib_data\MultiMatrixMobile.npz')

    ar_instance = AR_render("https://192.168.1.2:4343/video", cam_matrix, dist_coeff, r_vectors,t_vectors, './Models/Box/Box.obj', model_scale = 0.03)
    ar_instance.run() 