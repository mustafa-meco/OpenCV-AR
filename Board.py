import json
import numpy as np
import os

# Specify the path to the JSON file
file_path = "Boards_details\Boards.json"

# Read the JSON file
with open(file_path, "r") as file:
    data = json.load(file)


def prepare_cube_corners(d, mark_margin, mark_size):
    corners = d["corners"]
    MARGIN = mark_margin
    MARKER_SIZE = mark_size

    p = MARKER_SIZE/2

    for id in corners.keys():
        corners[id] = np.array(corners[id], dtype=np.float32)
        column_sum = np.sum(corners[id], axis=0)
        for point_i in range(len(corners[id])):
            for i in range(len(column_sum)):
                if column_sum[i] != 0:
                    corners[id][point_i][i] = corners[id][point_i][i]*(p+MARGIN)
                else:
                    corners[id][point_i][i] = corners[id][point_i][i]*p
    ids = corners.keys()
    corners = [corners[id] for id in ids]
    ids = np.array([[int(id)] for id in ids], dtype=np.int32)
    
    return corners, ids

# print(prepare_cube_corners(data[0], 0.001, 0.034))


def get_object_by_id(id, MARKER_SIZE=0.034, MARGIN=0.001):
    # global data
    # for d in data:
    #     corners=d["corners"]
    #     if id in corners.keys() or str(id) in corners.keys():
    #         if d["name"] == "Cube":
    #             board_corners, board_ids = prepare_cube_corners(d, MARGIN, MARKER_SIZE)
    #             return board_corners, board_ids, d["name"]
    # return None

    # Specify the path to the directory containing Boards_details
    directory_path = "Boards_details"

    # Get the names of the directories in Boards_details
    board_names = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]

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

        if [id] in ids or [str(id)] in ids:
            return corners, ids, board_name

        




# print(get_object_by_id(1))
# print(get_object_by_id(90))
# print(get_object_by_id("90"))
