#!/usr/bin/env python3

from argparse import ArgumentParser
import math
import pathlib

import cv2 as cv
import numpy as np

def red_delay_trackbar(x):
    global red_delay_frames
    red_delay_frames = x

def delay_ratio_trackbar(ratio):
    global delay_ratio
    delay_ratio = ratio

def jitter_speed_trackbar(j):
    global jitter_speed
    jitter_speed = j

def jitter_depth_trackbar(jd):
    global jitter_depth
    jitter_depth = jd

def bootstrap_trackbars():
    global delay_ratio, jitter_depth, jitter_speed, red_max_frames

    cv.createTrackbar('Red Delay Frames', 'frame', 0, red_max_frames - 1, red_delay_trackbar)
    cv.setTrackbarPos('Red Delay Frames', 'frame', red_delay_frames)

    cv.createTrackbar('Delay Ratio', 'frame', 0, 10, delay_ratio_trackbar)
    cv.setTrackbarPos('Delay Ratio', 'frame', delay_ratio)

    # Can't be 0 because we'll get a division by 0
    cv.createTrackbar('Jitter Speed', 'frame', 1, 10, jitter_speed_trackbar)
    cv.setTrackbarPos('Jitter Speed', 'frame', jitter_speed)

    # Tweaking this to allow negative values gives reverse time-travel, but it doesn't look great.
    cv.createTrackbar('Jitter Depth', 'frame', 0, 100, jitter_depth_trackbar)
    cv.setTrackbarPos('Jitter Depth', 'frame', jitter_depth)



if __name__ == '__main__':
    parser = ArgumentParser(
            prog='Vidrato',
            description='Chorus for your video',
            epilog='Made w/ <3 @ RC'
            )
    parser.add_argument('-i', '--interactive', default=False, action='store_true',
            help='enable trackbars')
    parser.add_argument('-m', '--no-mirror-monitor', default=True, action='store_false',
            dest='mirror_monitor',
            # We lie
            help="don't mirror output to monitor")
    parser.add_argument('-f', '--mirror-to-file', default=False, action='store_true',
            dest='mirror_file',
            help='mirror output to file')
    parser.add_argument('-o', '--out', type=pathlib.Path,
            help='Path to output file. Only mp4 supported at present.')
    args = parser.parse_args()

    #TODO: camera selection, delay ratio, red_max_frames, additional output codecs

    # Select camera 0
    #TODO allow camera selection and fail if unavailable
    cap = cv.VideoCapture(0)
    fps = cap.get(cv.CAP_PROP_FPS)
    R,G,B = 0,1,2
    # Read a frame to get our camera feed's dimensions
    _, frame = cap.read()
    y,x,_ = frame.shape
    # We need to show at least one frame in order to create trackbars
    cv.imshow('frame', frame)

    delay_ratio = 2
    red_max_frames = 30
    blue_max_frames = delay_ratio * red_max_frames
    # Decrement. 0 is no delay, so max range should be highest.
    # Current implementation would be equivalent to 0 mod red_max_frames without decrement.
    red_delay_frames = red_max_frames - 1
    blue_delay_frames = blue_max_frames - 1

    # Speed at which red_delay_frames is modulated
    # Jitter is applied by a Cosine wave with period 1 / (jitter_speed*FPS) frames.
    # e.g. for 15 FPS, the wave resets every 15 frames (period), so every second (frequency), if jitter_speed=1.
    # With jitter_speed=2, it resets every 30 frames, which takes two seconds.
    jitter_speed = 1
    # Depth of 0 to start with no jitter
    jitter_depth = 0

    # Initialize ring buffers
    red_queue = [np.zeros((y,x)) for _ in range(red_max_frames)]
    blue_queue = [np.zeros((y,x)) for _ in range(blue_max_frames)]
    red_w = 0
    red_r = (red_w - red_delay_frames) % red_max_frames
    blue_w = 0
    blue_r = (blue_w - blue_delay_frames) % blue_max_frames

    output = None
    if args.out is not None:
        # Write at half FPS, since I seem to be dropping frames here
        #TODO support additional codecs
        output = cv.VideoWriter(args.out,
                cv.VideoWriter_fourcc(*'mp4v'), fps / 2, (x, y))

    if args.interactive:
        bootstrap_trackbars()

    time_track = 0
    while True:
        # Catching Ctrl-C since the waitKey() line doesn't seem to be working on my laptop
        try:
            ret, frame = cap.read()

            jitter = (jitter_depth * ((math.sin(2 * math.pi * time_track / (jitter_speed * fps)) + 1) / 2)) / 100

            # We write, then read. In the case that red_w = red_r, we have a delay time of 0.
            # This is also why trackbar only goes to red_max_frames - 1:
            # If we didn't decrement, the "max" delay would wrap around and provide no delay.
            red_queue[red_w] = np.copy(frame[..., R])
            new_red_frame = np.copy(red_queue[red_r])
            frame[...,R] = new_red_frame
            red_w = (red_w + 1) % red_max_frames
            if jitter_depth == 0:
                red_r = (red_w - red_delay_frames) % red_max_frames
            else:
                red_r = (red_w - int(red_delay_frames * jitter)) % red_max_frames

            blue_queue[blue_w] = np.copy(frame[..., B])
            new_blue_frame = np.copy(blue_queue[blue_r])
            frame[...,B] = new_blue_frame
            blue_w = (blue_w + 1) % blue_max_frames
            blue_delay_frames = delay_ratio * red_delay_frames
            if jitter_depth == 0:
                blue_r = (blue_w - blue_delay_frames) % blue_max_frames
            else:
                blue_r = (blue_w - int(blue_delay_frames * jitter)) % blue_max_frames

            # Now mirror the result, show on screen, & write to file
            flipped = None
            if args.mirror_monitor or args.mirror_file:
                # Only compute if requested
                flipped = np.flip(frame, axis=1)

            cv.imshow('frame', flipped if args.mirror_monitor else frame)

            if args.out is not None:
                output.write(flipped if args.mirror_file else frame)

            time_track += 1

            if cv.waitKey(1) & 0xFF == ord('q'):
                break
        except KeyboardInterrupt:
            break


    if args.out is not None:
        output.release()
    cap.release()
    cv.destroyAllWindows()
