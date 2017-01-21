#!/usr/bin/env python

"""
Converts kalibr imu/camera calibration output to rovio's
configuration block format. Supports both radtan (AKA plumb_bob)
and FOV distorsion models.

NOTE: uses JPL convention for quaternions (rovio before the kindr
v1 update).
"""

import kalibr_common as kc

import numpy as np
import argparse
import sys
import rospkg


INTRINSICS_RADTAN_TPL = """

image_width: {resolution[0]}
image_height: {resolution[1]}
camera_name: cam{cam_index}
camera_matrix:
    rows: 3
    cols: 3
    data: [{intrinsics[0]}, 0.0, {intrinsics[2]}, 0.0, {intrinsics[1]}, {intrinsics[3]}, 0.0, 0.0, 1.0]
distortion_model: 'plumb_bob'
distortion_coefficients:
    rows: 1
    cols: 4
    data:  [{dist_params[0]}, {dist_params[1]}, {dist_params[2]}, {dist_params[3]}]

"""


INTRINSICS_FOV_TPL = """

image_width: {resolution[0]}
image_height: {resolution[1]}
camera_name: cam{cam_index}
camera_matrix:
    rows: 3
    cols: 3
    data: [{intrinsics[0]}, 0.0, {intrinsics[2]}, 0.0, {intrinsics[1]}, {intrinsics[3]}, 0.0, 0.0, 1.0]
distortion_model: fov
distortion_coefficients:
    rows: 1
    cols: 1
    data:  [{dist_params[0]}]

"""


EXTRINSICS_TPL = """

Camera{cam_index}
{{
    CalibrationFile
    qCM_x  {qCM[0]}       ; IMU-cam quat x  (JPL)
    qCM_y  {qCM[1]}       ; IMU-cam quat y  (JPL)
    qCM_z  {qCM[2]}       ; IMU-cam quat z  (JPL)
    qCM_w  {qCM[3]}       ; IMU-cam quat w  (JPL)
    MrMC_x {MrMC[0]}      ; IMU-cam vec x (in IMU CF) [m]
    MrMC_y {MrMC[1]}      ; IMU-cam vec x (in IMU CF) [m] [m]
    MrMC_z {MrMC[2]}      ; IMU-cam vec x (in IMU CF) [m] [m]
}}

"""


def do_camera_extrinsics(camchain, cam_index):
    format_args = dict(
        cam_index=cam_index,
        qCM=camchain.getExtrinsicsImuToCam(cam_index).q(),
        MrMC=camchain.getExtrinsicsImuToCam(cidx).inverse().T()[:,3],)
    return EXTRINSICS_TPL.format(**format_args)


def do_camera_intrinsics(camchain, cam_index):
    cam_params = camchain.getCameraParameters(cam_index)

    # NOTE: the switch from 'radtan' to 'plumb_bob' for rovio compatibility
    templates_by_model = {
        'radtan': INTRINSICS_RADTAN_TPL,
        'fov': INTRINSICS_FOV_TPL
    }

    tpl = templates_by_model[cam_params.getDistortion()[0]]

    return tpl.format(
        cam_index=cam_index,
        resolution=cam_params.getResolution(),
        intrinsics=cam_params.getIntrinsics()[1],
        dist_model=cam_params.getDistortion()[0],
        dist_params=cam_params.getDistortion()[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Convert a camchain_imu.yaml to rovio camera configuration block and intrinsics.')
    parser.add_argument('--cam', dest='yaml_path',
        help='Camera configuration as yaml file', required=True)
    parsed = parser.parse_args()

    # get an instance of RosPack with the default search paths
    rospack = rospkg.RosPack()

    # get the file path
    kalibr_path = rospack.get_path('kalibr')

    #load the camchain.yaml
    camchain = kc.ConfigReader.CameraChainParameters(parsed.yaml_path)

    for cidx in range(camchain.numCameras()):
        print do_camera_intrinsics(camchain, cidx)
        print('')
        print do_camera_extrinsics(camchain, cidx)
        print('')