#!/usr/bin/env python

"""
Creates a video out of sensor_msgs::Image messages stored in a bag.

Instead of creating temporary jpegs, like most other solution on the Internet,
we directly pipe the raw data into ffmpeg. Encodes to CRF-controlled mp4s by
default.

Make sure that the ffmpeg binary is available on PATH.
"""

import os.path
import rosbag
import sys
import argparse
import cv2
import numpy as np
import subprocess as sp

def parse_args():
    parser = argparse.ArgumentParser(
        prog='bag2movie.py',
        description='Creates a video out of sensor_msgs::Image messages stored in a bag.')
    parser.add_argument('--rate', type=int, help='video frame rate', default=20)
    parser.add_argument('--crf', type=int, help='Constant Rate Factor (CRF) for H264 encoding.', default=22)
    parser.add_argument('-t', type=str, dest='topic', help='topic where images are published')
    parser.add_argument('-o', type=str, dest='outfile', help='path to output file (w/ extension)', default=None)
    parser.add_argument('bagfile', type=str, help='path to the bagfile')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    bag = rosbag.Bag(args.bagfile)

    if not args.outfile:
        args.outfile = os.path.splitext(os.path.basename(args.bagfile))[0] + ".mp4"

    print("Saving output to '{}'".format(args.outfile))

    command = ['ffmpeg',
        '-y',  # Overwrites existing file

        # For compressed input (sensor_msgs::CompressedImage)
        # '-f', 'image2pipe',

        # For uncompressed input (sensor_msgs::Image)
        '-pix_fmt', 'bgr24',
        '-f', 'rawvideo',
        '-s', '752x480',

        '-i', 'pipe:0',
        '-vf', 'vflip',  # Flip input
        '-r', '{}'.format(args.rate),
        '-crf', str(args.crf),
        args.outfile]

    # bufsize = 0 makes life easier for ffmpeg
    pipe = sp.Popen(command, stdin=sp.PIPE, bufsize=0)

    for topic, msg, t in bag.read_messages([args.topic]):
        pipe.stdin.write(msg.data)

    pipe.terminate()


if __name__ == "__main__":
    main()