#!/usr/bin/env python3

from argparse import ArgumentParser
import math
import pathlib

import cv2 as cv
import numpy as np


def red_delay_trackbar(length):
    global red_delay_frames, delay_multiple
    red_delay_frames = length


def delay_multiple_trackbar(multiple):
    global delay_multiple
    delay_multiple = multiple


def mod_speed_trackbar(speed):
    global mod_speed
    mod_speed = speed


def mod_depth_trackbar(depth):
    global mod_depth
    mod_depth = depth


def bootstrap_trackbars():
    global delay_multiple, mod_depth, mod_speed, red_max_frames

    cv.createTrackbar('Red Delay Time (frames)', 'frame', red_max_frames, red_max_frames - 1, red_delay_trackbar)

    # This can't be 0 because of a divide-by-zero error, so we force this to be positive elsewhere
    cv.createTrackbar('Delay Multiple', 'frame', delay_multiple, 10, delay_multiple_trackbar)

    # Can't be 0 because we'll get a division by 0
    cv.createTrackbar('Jitter Speed', 'frame', mod_speed, 10, mod_speed_trackbar)

    # Tweaking this to allow negative values gives reverse time-travel, but it doesn't look great.
    cv.createTrackbar('Jitter Depth', 'frame', mod_depth, 100, mod_depth_trackbar)


if __name__ == '__main__':
    DELAY_MULTIPLE_MAX = 10

    parser = ArgumentParser(
            #prog='Vidrato',
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

    parser.add_argument('-l', '--delay-length', default=30, type=int,
            help='number of frames to delay by')
    parser.add_argument('-x', '--delay-multiple', default=2, type=int,
            help='blue_length = red_length * delay_multiple. Must be > 0.')

    # Speed at which red_delay_frames is modulated
    # Jitter is applied by a Cosine wave with period 1 / (mod_speed*FPS) frames.
    # e.g. for 15 FPS, the wave resets every 15 frames (period), so every second (frequency), if mod_speed=1.
    # With mod_speed=2, it resets every 30 frames, which takes two seconds.
    parser.add_argument('-s', '--mod-speed', default=1, type=int,
            help='rate of modulation effect')
    parser.add_argument('-d', '--mod-depth', default=0, type=int,
            help='depth of modulation effect (by default, 0, hence off)')
    args = parser.parse_args()

    # Validation:
    if args.delay_multiple < 1:
        import sys
        print(f'Error: delay multiple cannot be less than 1. Got {args.delay_multiple}.', file=sys.stderr)
        #parser.print_help(file=sys.stderr)
        sys.exit(1)

    delay_length = args.delay_length
    delay_multiple = args.delay_multiple
    mod_speed = args.mod_speed
    mod_depth = args.mod_depth

    #TODO: camera selection, additional output codecs

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

    red_max_frames = delay_length
    blue_max_frames = DELAY_MULTIPLE_MAX * red_max_frames
    # Decrement. 0 is no delay, so max range should be highest.
    # Current implementation would be equivalent to 0 mod red_max_frames without decrement.
    red_delay_frames = red_max_frames - 1
    blue_delay_frames = (delay_length * delay_multiple) - 1

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
        output = cv.VideoWriter(str(args.out),
                cv.VideoWriter_fourcc(*'mp4v'), fps, (x, y))

    if args.interactive:
        bootstrap_trackbars()

    time_track = 0
    while True:
        # Catching Ctrl-C since the waitKey() line doesn't seem to be working on my laptop
        try:
            ret, frame = cap.read()

            # Don't allow divide by zero
            # Sadly, we can't require the trackbar min to be anything but zero
            mod_speed = max(mod_speed, 1)
            jitter = (mod_depth * ((math.sin(2 * math.pi * time_track / (mod_speed * fps)) + 1) / 2)) / 100

            # We write, then read. In the case that red_w = red_r, we have a delay time of 0.
            # This is also why trackbar only goes to red_max_frames - 1:
            # If we didn't decrement, the "max" delay would wrap around and provide no delay.
            red_queue[red_w] = np.copy(frame[..., R])
            new_red_frame = np.copy(red_queue[red_r])
            frame[...,R] = new_red_frame
            red_w = (red_w + 1) % red_max_frames
            if mod_depth == 0:
                red_r = (red_w - red_delay_frames) % red_max_frames
            else:
                red_r = (red_w - int(red_delay_frames * jitter)) % red_max_frames

            blue_queue[blue_w] = np.copy(frame[..., B])
            new_blue_frame = np.copy(blue_queue[blue_r])
            frame[...,B] = new_blue_frame
            blue_w = (blue_w + 1) % blue_max_frames
            blue_delay_frames = delay_multiple * red_delay_frames
            if mod_depth == 0:
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
