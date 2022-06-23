import numpy as np
import cv2
import cv2.aruco as aruco
import sys, time, math

class PlaneDetection:
    def __init__(self, calib_path):
        """
        PlaneDetection object constructor. Initializes data containers.
        
        """
        self.id_to_find  = 0
        self.marker_size  = 2 #cm
        self.camera_matrix = np.loadtxt(calib_path+'camera_matrix.txt', delimiter=',')
        self.camera_distortion = np.loadtxt(calib_path+'distortion.txt', delimiter=',')
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.parameters = cv2.aruco.DetectorParameters_create()
        
        self.cube_vertices = {}
        self.homography = None

    def detect_tags_3D(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        corners, ids, rejected = cv2.aruco.detectMarkers(
                                            gray, 
                                            self.aruco_dict, 
                                            parameters = self.parameters,
                                            cameraMatrix = self.camera_matrix, 
                                            distCoeff = self.camera_distortion)

        if ids is not None and (self.id_to_find in ids):
            poses = cv2.aruco.estimatePoseSingleMarkers(
                                                corners, 
                                                self.marker_size, 
                                                self.camera_matrix, 
                                                self.camera_distortion)

            cv2.aruco.drawDetectedMarkers(frame, corners)
            grid_id = ids[0][0]
            self.rot_vecs, self.tran_vecs = poses[0], poses[1]
            self.cube_vertices = {str(tag_id[0]):pd.tag_z_vertices( 
                                                            self.rot_vecs[i][0], 
                                                            self.tran_vecs[i][0]) 
                                                            for i, tag_id in enumerate(ids)}
            for i, tag_id in enumerate(ids):
                # print(tag_id)
                rvec , tvec = self.rot_vecs[i][0], self.tran_vecs[i][0]
                self.draw_pose(frame, rvec, tvec)

                if tag_id == grid_id:
                    # draw_pose(frame, camera_matrix, camera_distortion, marker_size, rvec, tvec)
                    # draw_cube(frame, grid_id, camera_matrix, camera_distortion, marker_size, rvec, tvec)
                    self.draw_cube_update(frame, str(grid_id), rvec, tvec)
            del self.cube_vertices
	

    def draw_pose(self,image, rvec, tvec, z_rot=-1):
        world_points = np.array([
            4, 0, 0,
            0, 0, 0,
            0, 4, 0,
            0, 0, -4 * z_rot
        ]).reshape(-1, 1, 3) * 0.5 * self.marker_size

        img_points, _ = cv2.projectPoints(world_points, 
                                            rvec, tvec, 
                                            self.camera_matrix, 
                                            self.camera_distortion)
        img_points = np.round(img_points).astype(int)
        img_points = [tuple(pt) for pt in img_points.reshape(-1, 2)]

        cv2.line(image, img_points[0], img_points[1], (0,0,255), 2)
        cv2.line(image, img_points[1], img_points[2], (0,255,0), 2)
        cv2.line(image, img_points[1], img_points[3], (255,0,0), 2)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, 'X', img_points[0], font, 0.5, (0,0,255), 2, cv2.LINE_AA)
        cv2.putText(image, 'Y', img_points[2], font, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.putText(image, 'Z', img_points[3], font, 0.5, (255,0,0), 2, cv2.LINE_AA)
        cv2.putText(image, str((0,0)), (img_points[1][0]+10,img_points[1][1]-30), font, 0.5,
                                        (255, 255, 255), 1, cv2.LINE_AA)

    def define_world_pts(self,iD,grid_w, grid_h):
        
        if iD == 0:
            world_points = np.array([
                    0, 0, 0,
                    grid_w, 0, 0,
                    grid_w, -grid_h, 0,
                    0, -grid_h, 0,
                    0, 0, 3,
                    grid_w, 0, 3,
                    grid_w, -grid_h, 3,
                    0, -grid_h, 3
                ]).reshape(-1, 1, 3) 
            
        if iD == 1:
            world_points = np.array([
                    0, 0, 0,
                    0, -grid_h, 0,
                    -grid_w, -grid_h, 0,
                    -grid_w, 0, 0,
                    0, 0, 3,
                    0, -grid_h, 3,
                    -grid_w, -grid_h, 3,
                    -grid_w, 0, 3
                ]).reshape(-1, 1, 3)
            
        if iD == 2:
            world_points = np.array([
                    0, 0, 0,
                    -grid_w, 0, 0,
                    -grid_w, grid_h, 0,
                    0, grid_h, 0,
                    0, 0, 3,
                    -grid_w, 0, 3,
                    -grid_w, grid_h, 3,
                    0, grid_h, 3,
                ]).reshape(-1, 1, 3)
            
        if iD == 3:
            world_points = np.array([
                    0, 0, 0,
                    0, grid_h, 0,
                    grid_w, grid_h, 0,
                    grid_w, 0, 0,
                    0, 0, 3,
                    0, grid_h, 3,
                    grid_w, grid_h, 3,
                    grid_w, 0, 3
                    
                ]).reshape(-1, 1, 3)
            
        if iD == 4:
            world_points = np.array([
                    12.75, 7, 0,
                    -12.75, 7, 0,
                    -12.75, -7, 0,
                    12.75, -7, 0,
                    12.75, 7, 3,
                    -12.75, 7, 3,
                    -12.75, -7, 3,
                    12.75, -7, 3,
                ]).reshape(-1, 1, 3)
        # print(world_points)
        return world_points * 0.5 * self.marker_size
    def draw_cube(self,image, iD , rvec, tvec):
        grid_w = 25.5
        grid_h = 14.0
        world_points = self.define_world_pts(iD, grid_w, grid_h, self.marker_size)
        img_points, _ = cv2.projectPoints(world_points, rvec, tvec, self.camera_matrix, self.camera_distortion)
        img_points = np.round(img_points).astype(int)
        # print(img_points)
        img_points = [tuple(pt) for pt in img_points.reshape(-1, 2)] # -> [(x1,y1),(x2,y2),...] in pixels
        
        cv2.line(image, img_points[0], img_points[1], (255,0,0), 2)
        cv2.line(image, img_points[1], img_points[2], (255,0,0), 2)
        cv2.line(image, img_points[2], img_points[3], (255,0,0), 2)
        cv2.line(image, img_points[3], img_points[0], (255,0,0), 2)
        cv2.line(image, img_points[4], img_points[5], (255,0,0), 2)
        cv2.line(image, img_points[5], img_points[6], (255,0,0), 2)
        cv2.line(image, img_points[6], img_points[7], (255,0,0), 2)
        cv2.line(image, img_points[7], img_points[4], (255,0,0), 2)
        cv2.line(image, img_points[0], img_points[4], (255,0,0), 2)
        cv2.line(image, img_points[1], img_points[5], (255,0,0), 2)
        cv2.line(image, img_points[2], img_points[6], (255,0,0), 2)
        cv2.line(image, img_points[3], img_points[7], (255,0,0), 2)

    def tag_z_vertices(self, rvec, tvec, z_rot=-1):
        world_points = np.array([
            0, 0, 0,
            0, 0, -3 * z_rot
        ]).reshape(-1, 1, 3) * 0.5 * self.marker_size

        img_points, _ = cv2.projectPoints(world_points, rvec, tvec, self.camera_matrix, self.camera_distortion)
        img_points = np.round(img_points).astype(int)
        img_points = [tuple(pt) for pt in img_points.reshape(-1, 2)]

        return img_points[0],img_points[1]
    def define_image_pts(self,iD,grid_w, grid_h, cube_vertices, rvec, tvec):
        
        points_update = [None,None,None,None,None,None,None,None]
        vert_2_update = list(cube_vertices.keys())

        if iD == '0':
            if '1' in vert_2_update:
                points_update[1] = cube_vertices['1'][0]
                points_update[5] = cube_vertices['1'][1]
            if '2' in vert_2_update:
                points_update[2] = cube_vertices['2'][0]
                points_update[6] = cube_vertices['2'][1]
            if '3' in vert_2_update:
                points_update[3] = cube_vertices['3'][0]
                points_update[7] = cube_vertices['3'][1]
            world_points = np.array([
                    0, 0, 0,
                    grid_w, 0, 0,
                    grid_w, -grid_h, 0,
                    0, -grid_h, 0,
                    0, 0, 3,
                    grid_w, 0, 3,
                    grid_w, -grid_h, 3,
                    0, -grid_h, 3
                ]).reshape(-1, 1, 3)
            
        if iD == '1':
            if '2' in vert_2_update:
                points_update[1] = cube_vertices['2'][0]
                points_update[5] = cube_vertices['2'][1]
            if '3' in vert_2_update:
                points_update[2] = cube_vertices['3'][0]
                points_update[6] = cube_vertices['3'][1]
            if '0' in vert_2_update:
                points_update[3] = cube_vertices['0'][0]
                points_update[7] = cube_vertices['0'][1]
            world_points = np.array([
                    0, 0, 0,
                    0, -grid_h, 0,
                    -grid_w, -grid_h, 0,
                    -grid_w, 0, 0,
                    0, 0, 3,
                    0, -grid_h, 3,
                    -grid_w, -grid_h, 3,
                    -grid_w, 0, 3
                ]).reshape(-1, 1, 3)
            
        if iD == '2':
            if '3' in vert_2_update:
                points_update[1] = cube_vertices['3'][0]
                points_update[5] = cube_vertices['3'][1]
            if '0' in vert_2_update:
                points_update[2] = cube_vertices['0'][0]
                points_update[6] = cube_vertices['0'][1]
            if '1' in vert_2_update:
                points_update[3] = cube_vertices['1'][0]
                points_update[7] = cube_vertices['1'][1]
            world_points = np.array([
                    0, 0, 0,
                    -grid_w, 0, 0,
                    -grid_w, grid_h, 0,
                    0, grid_h, 0,
                    0, 0, 3,
                    -grid_w, 0, 3,
                    -grid_w, grid_h, 3,
                    0, grid_h, 3,
                ]).reshape(-1, 1, 3)
            
        if iD == '3':
            if '0' in vert_2_update:
                points_update[1] = cube_vertices['0'][0]
                points_update[5] = cube_vertices['0'][1]
            if '1' in vert_2_update:
                points_update[2] = cube_vertices['1'][0]
                points_update[6] = cube_vertices['1'][1]
            if '2' in vert_2_update:
                points_update[3] = cube_vertices['2'][0]
                points_update[7] = cube_vertices['2'][1]
            world_points = np.array([
                    0, 0, 0,
                    0, grid_h, 0,
                    grid_w, grid_h, 0,
                    grid_w, 0, 0,
                    0, 0, 3,
                    0, grid_h, 3,
                    grid_w, grid_h, 3,
                    grid_w, 0, 3
                    
                ]).reshape(-1, 1, 3)
            
        if iD == '4':
            if '0' in vert_2_update:
                points_update[0] = cube_vertices['0'][0]
                points_update[4] = cube_vertices['0'][1]
            if '1' in vert_2_update:
                points_update[1] = cube_vertices['1'][0]
                points_update[5] = cube_vertices['1'][1]
            if '2' in vert_2_update:
                points_update[2] = cube_vertices['2'][0]
                points_update[6] = cube_vertices['2'][1]
            if '3' in vert_2_update:
                points_update[3] = cube_vertices['3'][0]
                points_update[7] = cube_vertices['3'][1]
            world_points = np.array([
                    -12.75, 7, 0,
                    12.75, 7, 0,
                    12.75, -7, 0,
                    -12.75, -7, 0,
                    -12.75, 7, 3,
                    12.75, 7, 3,
                    12.75, -7, 3,
                    -12.75, -7, 3
                    
                ]).reshape(-1, 1, 3)

        world_points = world_points * 0.5 * self.marker_size
        img_points, _ = cv2.projectPoints(world_points, rvec, tvec, self.camera_matrix, self.camera_distortion)
        img_points = np.round(img_points).astype(int)
        img_points = [ points_update[i] if points_update[i] else tuple(pt) for i, pt in enumerate(img_points.reshape(-1, 2))] # -> [(x1,y1),(x2,y2),...] in pixels
        # print(points_update)
        return img_points

    def draw_cube_update(self,image, iD, rvec, tvec):
        grid_w = 23.5
        grid_h = 13.0
        # print(iD)
        img_points = self.define_image_pts(str(iD), grid_w, grid_h, self.cube_vertices, rvec, tvec)

        cv2.line(image, img_points[0], img_points[1], (255,0,0), 2)
        cv2.line(image, img_points[1], img_points[2], (255,0,0), 2)
        cv2.line(image, img_points[2], img_points[3], (255,0,0), 2)
        cv2.line(image, img_points[3], img_points[0], (255,0,0), 2)
        cv2.line(image, img_points[4], img_points[5], (255,0,0), 2)
        cv2.line(image, img_points[5], img_points[6], (255,0,0), 2)
        cv2.line(image, img_points[6], img_points[7], (255,0,0), 2)
        cv2.line(image, img_points[7], img_points[4], (255,0,0), 2)
        cv2.line(image, img_points[0], img_points[4], (255,0,0), 2)
        cv2.line(image, img_points[1], img_points[5], (255,0,0), 2)
        cv2.line(image, img_points[2], img_points[6], (255,0,0), 2)
        cv2.line(image, img_points[3], img_points[7], (255,0,0), 2)

calib_path = ""

pd = PlaneDetection(calib_path)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:

    ret, frame = cap.read()

    pd.detect_tags_3D(frame)
            
    cv2.imshow('frame', frame)

    key = cv2.waitKey(1) & 0xFF
    
    if key == 27:
        cap.release()
        cv2.destroyAllWindows()
        break