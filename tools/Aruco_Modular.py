import cv2 as cv
from cv2 import aruco
import numpy as np

def _get_corners(corners):
    corners = corners.reshape(4, 2)
    corners = corners.astype(int)
    tr = corners[1].ravel()
    tl = corners[0].ravel()
    br = corners[2].ravel()
    bl = corners[3].ravel()

    return tl, tr, br, bl


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

def setup_detector(markerSize=0, totalMarkers=0):
    """
    Setup the Aruco marker detector.
    :param markerSize: (int) Size of the marker.
    :param totalMarkers: (int) Total number of markers.
    :return: (cv2.aruco_Dictionary) Aruco marker dictionary.
    :return: (cv2.aruco_DetectorParameters) Aruco marker detector parameters.
    """
    if markerSize == 0 or total_markers == 0:
        key = getattr(aruco, f'DICT_ARUCO_ORIGINAL')
    else:
        key = getattr(aruco, f'DICT_{markerSize}X{markerSize}_{totalMarkers}')
    arucoDict = aruco.getPredefinedDictionary(key)

    arucoParam = aruco.DetectorParameters()

    return arucoDict, arucoParam

def findArucoMarkers(img, arucoDict, arucoParam, draw=True, convgray=True):
    """
    Find the Aruco markers in the image.
    :param img: (np.array) Input image.
    :param arucoDict: (cv2.aruco_Dictionary) Aruco marker dictionary.
    :param arucoParam: (cv2.aruco_DetectorParameters) Aruco marker detector parameters.
    :param draw: (bool) Whether to draw the detected markers on the image.
    :param convgray: (bool) Whether to convert the image to grayscale.
    :return: (List of np.array) Corners of the detected markers.
    :return: (np.array) IDs of the detected markers.
    :return: (np.array) Rejected candidates.
    """
    if convgray:
        imgGray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    else:
        imgGray = img

    bboxs, ids, rejected = aruco.detectMarkers(imgGray, arucoDict, parameters=arucoParam)
    
    # print(ids)

    if draw:
        aruco.drawDetectedMarkers(img, bboxs)

    return bboxs, ids, rejected

def setup_camera(device_idx):
    """
    Set up the camera using OpenCV's VideoCapture class
    
    Parameters:
    device_idx (int): index of the camera device
    
    Returns:
    cv2.VideoCapture: a VideoCapture object representing the camera
    """
    cap = cv.VideoCapture(device_idx)
    return cap

def estimate_single_marker_pose(marker_corners, cam_mat, dist_coef, MARKER_SIZE):
    """
    Estimate the pose of a single marker.
    :param marker_corners: (List of np.array) Corners of the marker.
    :param cam_mat: (np.array) Camera matrix.
    :param dist_coef: (np.array) Distortion coefficients.
    :param MARKER_SIZE: (int) Size of the marker.
    :return: (np.array) Rotation vector.
    :return: (np.array) Translation vector.
    # :return: (np.array) Image points.
    """
    rVec, tVec, _ = aruco.estimatePoseSingleMarkers(
            marker_corners, MARKER_SIZE, cam_mat, dist_coef
        )
    return rVec, tVec

def draw_marker_corners(frame, marker_corners):
    """
    Draws the marker corners on the frame.
    :param frame: (np.array) Input frame.
    :param marker_corners: (List of np.array) Corners of the marker.
    :return: (np.array) Frame with marker corners drawn.
    """
    for corners in marker_corners:
        cv.polylines(
            frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv.LINE_AA
        )
    return frame

def draw_marker_pose(frame, corners, distance, id):
    """
    Draws the pose of the marker on the frame.
    :param frame: (np.array) Input frame.
    :param corners: (np.array) Corners of the marker.
    :param distance: (float) Distance of the marker from the camera.
    :return: (np.array) Frame with marker pose drawn.
    """
    cv.polylines(
        frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv.LINE_AA
    )
    top_left, top_right, bottom_right, bottom_left = _get_corners(corners)

    cv.putText(
        frame,
        f"id: {id} Dist: {round(distance, 2)}",
        top_right,
        cv.FONT_HERSHEY_PLAIN,
        1.3,
        (0, 0, 255),
        2,
        cv.LINE_AA,
    )
    return frame

def augmentAruco(corners, id, img, imgAug, drawId=True):
    tl, tr, br, bl = _get_corners(corners)

    h, w, c = imgAug.shape

    pts1 = np.array([tl, tr, br, bl])
    pts2 = np.float32([[0,0], [w,0], [w,h], [0,h]])
    matrix, _ = cv.findHomography(pts2, pts1)
    # print(f"matrix: {matrix}")
    imgOut = cv.warpPerspective(imgAug, matrix, (img.shape[1], img.shape[0]))

    cv.fillConvexPoly(img, pts1.astype(int), (0,0,0))
    imgOut = img + imgOut

    if drawId:
        cv.putText(imgOut, str(id), (tl[0],tl[1]), cv.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)

    return imgOut 





if __name__ == '__main__':

    cam_mat, dist_coef, r_vectors, t_vectors = load_calib_data("./calib_data/MultiMatrixMobile.npz")

    MARKER_SIZE = 3.6  # centimeters
    MARKER_BIT_SIZE = 0
    MARKERS_COUNT = 0

    marker_dict, param_markers = setup_detector(MARKER_BIT_SIZE, MARKERS_COUNT)

    cap = setup_camera(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # Detect Aruco markers
        marker_corners, marker_IDs, reject = findArucoMarkers(frame, marker_dict, param_markers)
        if marker_corners:
            rVec, tVec = estimate_single_marker_pose(marker_corners, cam_mat, dist_coef)
            total_markers = range(0, marker_IDs.size)

            for ids, corners, i in zip(marker_IDs, marker_corners, total_markers):         

                distance = np.sqrt(
                    tVec[i][0][2] ** 2 + tVec[i][0][0] ** 2 + tVec[i][0][1] ** 2
                )
                
                # Draw the pose of the marker
                point = cv.drawFrameAxes(frame, cam_mat, dist_coef, rVec[i], tVec[i], 4, 4)
                frame = draw_marker_pose(frame, corners, distance, ids)
                print(f"Rotation Vector: {rVec},\n Translational Vector: {tVec}")
                
                # print(ids, "  ", corners)
        cv.imshow("frame", frame)
        key = cv.waitKey(1)
        if key == ord("q"):
            break
    cap.release()
    cv.destroyAllWindows()