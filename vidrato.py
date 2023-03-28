#!/usr/bin/env python3

import math

import cv2 as cv
import numpy as np

# Mirrors on-screen video when True.
mirror_monitor = True
# Mirrors file output when this is True AND mirror_monitor is also True
mirror_file = False
# Where to write output
#outfile = "redblue_delay.webm" # Sadness
outfile = "out/output.mp4"

# Select camera 0
cap = cv.VideoCapture(0)
fps = cap.get(cv.CAP_PROP_FPS)
R,G,B = 0,1,2

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

# Read a frame to get our camera feed's dimensions
_, frame = cap.read()
y,x,_ = frame.shape

# Write at half FPS, since I seem to be dropping frames here
output = cv.VideoWriter(outfile,
        cv.VideoWriter_fourcc(*'mp4v'), fps / 2, (x, y))
        #cv.VideoWriter_fourcc(*'VP09'), fps, (x, y)) # :(

delay_ratio = 2
red_max_frames = 30
blue_max_frames = delay_ratio * red_max_frames
red_delay_frames = red_max_frames
blue_delay_frames = blue_max_frames

# Speed at which red_delay_frames is modulated
# Jitter is applied by a Cosine wave with period 1 / (jitter_speed*FPS) frames.
# e.g. for 15 FPS, the wave resets every 15 frames (period), so every second (frequency), if jitter_speed=1.
# With jitter_speed=2, it resets every 30 frames, which takes two seconds.
jitter_speed = 1
# Depth of 0 to start with no jitter
jitter_depth = 0


red_queue = [np.zeros((y,x)) for _ in range(red_max_frames)]
blue_queue = [np.zeros((y,x)) for _ in range(blue_max_frames)]

red_w = 0
red_r = (red_w - red_delay_frames) % red_max_frames
blue_w = 0
blue_r = (blue_w - blue_delay_frames) % blue_max_frames

# We need to show the current frame once in order to create the trackbar
cv.imshow('frame', frame)
cv.createTrackbar('Red Delay Frames', 'frame', 0, red_max_frames - 1, red_delay_trackbar)
cv.setTrackbarPos('Red Delay Frames', 'frame', red_delay_frames)
cv.createTrackbar('Delay Ratio', 'frame', 0, 10, delay_ratio_trackbar)
cv.setTrackbarPos('Delay Ratio', 'frame', delay_ratio)

# Can't be 0 because we'll get a division by 0
cv.createTrackbar('Jitter Speed', 'frame', 1, 10, jitter_speed_trackbar)
cv.setTrackbarPos('Jitter Speed', 'frame', jitter_speed)
# I think allowing negatives could be funny - it would cause reverse time travel!
#cv.createTrackbar('Jitter Depth', 'frame', 0, 10, jitter_depth_trackbar)
cv.createTrackbar('Jitter Depth', 'frame', 0, 100, jitter_depth_trackbar)
cv.setTrackbarPos('Jitter Depth', 'frame', jitter_depth)

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
        monitor_out = np.flip(frame, axis=1) if mirror_monitor else frame
        cv.imshow('frame', monitor_out)
        file_out = monitor_out if mirror_file else frame
        output.write(file_out)

        time_track += 1

        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    except KeyboardInterrupt:
        break


# Clean up
print(f'Cleaning up and writing {outfile}')
output.release()
cap.release()
cv.destroyAllWindows()
