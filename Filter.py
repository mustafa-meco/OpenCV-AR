import numpy as np
class Filter:
    def __init__(self):
        self.pre_trans_x = None
        self.pre_trans_y = None
        self.pre_trans_z = None
        
    def update(self, tvecs) -> bool:
        trans_x, trans_y, trans_z = tvecs[0][0][0], tvecs[0][0][1], tvecs[0][0][2]
        is_mark_move = False
        if self.pre_trans_x is not None:
            if abs(self.pre_trans_x - trans_x) > 0.001 or abs(self.pre_trans_y - trans_y) > 0.002 or abs(self.pre_trans_z - trans_z) > 0.015:
                dis_x = abs(self.pre_trans_x - trans_x)
                dis_y = abs(self.pre_trans_y - trans_y)
                dis_z = abs(self.pre_trans_z - trans_z)
                # if dis_x > 0.001:
                #     print('dis_x', dis_x)
                # if dis_y > 0.001:
                #     print("dis_y", dis_y)
                # if dis_z > 0.001:
                #     print("dis_z", dis_z)
                
                is_mark_move = True
        self.pre_trans_x, self.pre_trans_y, self.pre_trans_z = trans_x, trans_y, trans_z
        return is_mark_move

    def update_board(self, tvecs):
        if tvecs.shape[0] > 3:
            tvecs = tvecs[0]
        trans_x, trans_y, trans_z = tvecs[0][0], tvecs[1][0], tvecs[2][0]
        is_mark_move = False
        if self.pre_trans_x is not None:
            if abs(self.pre_trans_x - trans_x) > 0.001 or abs(self.pre_trans_y - trans_y) > 0.002 or abs(self.pre_trans_z - trans_z) > 0.015:
                dis_x = abs(self.pre_trans_x - trans_x)
                dis_y = abs(self.pre_trans_y - trans_y)
                dis_z = abs(self.pre_trans_z - trans_z)
                # if dis_x > 0.001:
                #     print('dis_x', dis_x)
                # if dis_y > 0.001:
                #     print("dis_y", dis_y)
                # if dis_z > 0.001:
                #     print("dis_z", dis_z)
                
                is_mark_move = True
        self.pre_trans_x, self.pre_trans_y, self.pre_trans_z = trans_x, trans_y, trans_z
        return is_mark_move

    def ids_corners_by_object(self, ids, corners, board_ids):
        # print('ids', ids)
        # print(type(ids))
        # print(type(ids[0]))
        # print('corners', corners)
        # print('board_ids', board_ids)
        new_ids = []
        new_corners = []
        for i in range(len(ids)):
            for j in range(len(board_ids)):
                if ids[i] == board_ids[j]:
                    new_ids.append(ids[i])
                    new_corners.append(corners[i])

        # print('new_ids', new_ids)
        # print(type(new_ids))
        # print(type(new_ids[0]))
        new_ids = np.array(new_ids)
        return new_ids, tuple(new_corners)

