from Board import *
import numpy as np
import os


board_corners, board_ids, name = get_object_by_id(90)


# Write board_corners to a file
np.save('Boards_details/Cube34/board_corners.npy', board_corners)

# Write board_ids to a file
np.save('Boards_details/Cube34/board_ids.npy', board_ids)

MARKER_SIZE = 0.020
p = MARKER_SIZE/2

def get_square_corners(center_point, side_length, constant_axis, flip=False):
    x, y, z = center_point
    half_length = side_length / 2
    if constant_axis == 'x':
        if not flip:
            top_left = [x, y - half_length, z + half_length]
            top_right = [x, y + half_length, z + half_length]
            bottom_left = [x, y - half_length, z - half_length]
            bottom_right = [x, y + half_length, z - half_length]
            return [top_left, top_right, bottom_right, bottom_left]
        else:
            top_left = [x, y + half_length, z + half_length]
            top_right = [x, y - half_length, z + half_length]
            bottom_left = [x, y + half_length, z - half_length]
            bottom_right = [x, y - half_length, z - half_length]
            return [bottom_right, bottom_left, top_left, top_right]
    elif constant_axis == 'y':
        if not flip:
            top_left = [x - half_length, y, z + half_length]
            top_right = [x + half_length, y, z + half_length]
            bottom_left = [x - half_length, y, z - half_length]
            bottom_right = [x + half_length, y, z - half_length]
            return [top_left, top_right, bottom_right, bottom_left]
        else:
            top_left = [x + half_length, y, z + half_length]
            top_right = [x - half_length, y, z + half_length]
            bottom_left = [x + half_length, y, z - half_length]
            bottom_right = [x - half_length, y, z - half_length]
            return [top_left, top_right, bottom_right, bottom_left]
    elif constant_axis == 'z':
        if not flip:
            top_left = [x - half_length, y - half_length, z]
            top_right = [x - half_length, y + half_length, z]
            bottom_left = [x + half_length, y - half_length, z]
            bottom_right = [x + half_length, y + half_length, z]
            return [top_left, top_right, bottom_right, bottom_left]
        else:
            top_left = [x + half_length, y - half_length, z]
            top_right = [x + half_length, y + half_length, z]
            bottom_left = [x - half_length, y - half_length, z]
            bottom_right = [x - half_length, y + half_length, z]
            return [top_left, top_right, bottom_right, bottom_left]

front_points = get_square_corners((0.025, 0, 0), 0.0125*2, 'x')
back_points = get_square_corners((-0.025, 0, 0), 0.0125*2, 'x')
back_points = [back_points[1], back_points[0], back_points[3], back_points[2]]
left_points = get_square_corners((0, -0.025, 0), 0.0125*2, 'y')
right_points = get_square_corners((0, 0.025, 0), 0.0125*2, 'y', True)
top_points = get_square_corners((0, 0, 0.025), 0.0125*2, 'z')
bottom_points = get_square_corners((0, 0, -0.025), 0.0125*2, 'z', True)

# Cube Board
board_corners = [
    # front
    np.array(get_square_corners(f, MARKER_SIZE, 'x'), dtype=np.float32) for f in front_points
] + [
    # back
    np.array(get_square_corners(b, MARKER_SIZE, 'x', True), dtype=np.float32) for b in back_points
] + [
    # left
    np.array(get_square_corners(l, MARKER_SIZE, 'y'), dtype=np.float32) for l in left_points
] + [
    # right
    np.array(get_square_corners(r, MARKER_SIZE, 'y', True), dtype=np.float32) for r in right_points
] + [
    # top
    np.array(get_square_corners(t, MARKER_SIZE, 'z'), dtype=np.float32) for t in top_points
] + [
    # bottom
    np.array(get_square_corners(b, MARKER_SIZE, 'z', True), dtype=np.float32) for b in bottom_points
]


board_ids = np.array( [[208],[209],[211],[210],[219],[218],[216],[217],[224],[225],[227],[226],[228],[229],[231],[230],[220],[221],[223],[222],[212],[213],[215],[214]], dtype=np.int32)

# Create directory if not found
directory = 'Boards_details/Cube2x2'
if not os.path.exists(directory):
    os.makedirs(directory)

# Write board_corners to a file
np.save(os.path.join(directory, 'board_corners.npy'), board_corners)

# Write board_ids to a file
np.save(os.path.join(directory, 'board_ids.npy'), board_ids)

# Write board_corners to a file
np.save('Boards_details/Cube2x2/board_corners.npy', board_corners)

# Write board_ids to a file
np.save('Boards_details/Cube2x2/board_ids.npy', board_ids)


# cuboid
BOARD_w = 0.0475
BOARD_h = 0.0285
MARGIN_in = 0.0045
MARGIN_out = 0.002
p_w = BOARD_w/2
p_h = BOARD_h/2
MARKER_SIZE = 0.0185
p = MARKER_SIZE/2
# Cube Board
board_corners3 = [
    # top
    np.array([[-p, -MARKER_SIZE-MARGIN_in, p_h], [-p, -MARGIN_in, p_h], [p, -MARGIN_in, p_h], [p, -MARKER_SIZE-MARGIN_in, p_h]],dtype=np.float32),
    np.array([[-p, MARGIN_in, p_h], [-p, MARKER_SIZE+MARGIN_in, p_h], [p, MARKER_SIZE+MARGIN_in, p_h], [p, MARGIN_in, p_h]],dtype=np.float32),
    # front
    np.array([[p_h, -MARKER_SIZE-MARGIN_in, p], [p_h, -MARGIN_in, p], [p_h, -MARGIN_in, -p], [p_h, -MARKER_SIZE-MARGIN_in, -p]],dtype=np.float32),
    np.array([[p_h, MARGIN_in, p], [p_h, MARKER_SIZE+MARGIN_in, p], [p_h, MARKER_SIZE+MARGIN_in, -p], [p_h, MARGIN_in, -p]],dtype=np.float32),
    # back
    np.array([[-p_h, -MARKER_SIZE-MARGIN_in, -p], [-p_h, -MARGIN_in, -p], [-p_h, -MARGIN_in, p], [-p_h, -MARKER_SIZE-MARGIN_in, p]],dtype=np.float32),
    np.array([[-p_h, MARGIN_in, -p], [-p_h, MARKER_SIZE+MARGIN_in, -p], [-p_h, MARKER_SIZE+MARGIN_in, p], [-p_h, MARGIN_in, p]],dtype=np.float32),
    # bottom
    np.array([[-p, MARKER_SIZE+MARGIN_in, -p_h], [-p, MARGIN_in, -p_h], [p, MARGIN_in, -p_h], [p, MARKER_SIZE+MARGIN_in, -p_h]],dtype=np.float32),
    np.array([[-p, -MARGIN_in, -p_h], [-p, -MARKER_SIZE-MARGIN_in, -p_h], [p, -MARKER_SIZE-MARGIN_in, -p_h], [p, -MARGIN_in, -p_h]],dtype=np.float32),
    

    ]

board_ids3 = np.array( [[200],[201],[206],[207],[202],[203],[204],[205]], dtype=np.int32)

# Create directory if not found
directory = 'Boards_details/Cuboid'
if not os.path.exists(directory):
    os.makedirs(directory)

# Write board_corners to a file
np.save(os.path.join(directory, 'board_corners.npy'), board_corners3)

# Write board_ids to a file
np.save(os.path.join(directory, 'board_ids.npy'), board_ids3)

# Write board_corners to a file
np.save('Boards_details/Cuboid/board_corners.npy', board_corners3)

# Write board_ids to a file
np.save('Boards_details/Cuboid/board_ids.npy', board_ids3)


def cylcor_to_xyz(r, theta, z):
    x = r * np.sin(theta)
    y = r * np.cos(theta)
    return [x, y, z]

MARGIN = 0.0045
MARKER_SIZE = 0.019
Cylinder_diameter = 0.064
r = Cylinder_diameter/2

board_corners4 = [
    np.array([cylcor_to_xyz(r, k*(MARGIN+MARKER_SIZE)/r, j*(MARKER_SIZE+MARGIN)),cylcor_to_xyz(r, (k*(MARGIN+MARKER_SIZE)/r)+MARKER_SIZE/r, j*(MARKER_SIZE+MARGIN)), cylcor_to_xyz(r, (k*(MARGIN+MARKER_SIZE)/r)+MARKER_SIZE/r, j*(MARKER_SIZE+MARGIN)+MARKER_SIZE),  cylcor_to_xyz(r, k*(MARGIN+MARKER_SIZE)/r, j*(MARKER_SIZE+MARGIN)+MARKER_SIZE) ],dtype=np.float32) for k in range(8) for j in range(6) 
 ]


board_ids4 = np.array( [[(j+6)+(k*6)]  for k in range(8) for j in range(6)], dtype=np.int32)

# Create directory if not found
directory = 'Boards_details/Cylinder'
if not os.path.exists(directory):
    os.makedirs(directory)

# Write board_corners to a file
np.save(os.path.join(directory, 'board_corners.npy'), board_corners4)

# Write board_ids to a file
np.save(os.path.join(directory, 'board_ids.npy'), board_ids4)

# Write board_corners to a file
np.save('Boards_details/Cylinder/board_corners.npy', board_corners4)

# Write board_ids to a file
np.save('Boards_details/Cylinder/board_ids.npy', board_ids4)