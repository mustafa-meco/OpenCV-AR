import numpy as np
import cv2
def extrinsic2ModelView(RVEC, TVEC, R_vector = True):
    """[Get modelview matrix from RVEC and TVEC]

    Arguments:
        RVEC {[vector]} -- [Rotation vector]
        TVEC {[vector]} -- [Translation vector]
    """
    # print("RVEC", RVEC.shape)
    # print("-------------------")
    # print("TVEC", TVEC.shape)
    # if RVEC.shape[0] > 3:
    #     RVEC = RVEC[0]
    # if TVEC.shape[0] > 3:
    #     TVEC = TVEC[0]
    
    R, _ = cv2.Rodrigues(RVEC)
    
    Rx = np.array([
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, -1]
    ])

    TVEC = TVEC.flatten().reshape((3, 1))

    
    transform_matrix = Rx @ np.hstack((R, TVEC))
    M = np.eye(4)
    M[:3, :] = transform_matrix
    return M.T.flatten()


def intrinsic2Project(MTX, width, height, near_plane=0.01, far_plane=100.0):
    """[Get ]

    Arguments:
        MTX {[np.array]} -- [The camera instrinsic matrix that you get from calibrating your chessboard]
        width {[float]} -- [width of viewport]]
        height {[float]} -- [height of viewport]

    Keyword Arguments:
        near_plane {float} -- [near_plane] (default: {0.01})
        far_plane {float} -- [far plane] (default: {100.0})

    Returns:
        [np.array] -- [1 dim array of project matrix]
    """
    P = np.zeros(shape=(4, 4), dtype=np.float32) # Projection matrix to be returned to OpenGL  
    
    fx, fy = MTX[0, 0], MTX[1, 1] # Focal length in x and y axis  
    cx, cy = MTX[0, 2], MTX[1, 2] # Optical center in x and y axis  
    
    
    P[0, 0] = 2 * fx / width # Scale the x axis 
    P[1, 1] = 2 * fy / height # Scale the y axis
    P[2, 0] = 1 - 2 * cx / width # Translate the x axis
    P[2, 1] = 2 * cy / height - 1 # Translate the y axis
    P[2, 2] = -(far_plane + near_plane) / (far_plane - near_plane) # Translate the z axis
    P[2, 3] = -1.0 # Set w = -z
    P[3, 2] = - (2 * far_plane * near_plane) / (far_plane - near_plane) # Set z = 0 
    # P should be a 4x4 matrix, but OpenGL expects a 16-element array (column-major)
    # So, we flatten P and return it as a 16-element array  
    # ex. P = [2 * fx / width,     0,                    0,                                                         0,
    #         0,                   2 * fy / height,      0,                                                         0,
    #         1 - 2 * cx / width,  2 * cy / height - 1,  -(far_plane + near_plane) / (far_plane - near_plane),      -1,
    #         0,                   0,                    -(2 * far_plane * near_plane) / (far_plane - near_plane),  0]

    return P.flatten()
