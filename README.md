# Vidrato
Vidrato is a [chorus](https://en.wikipedia.org/wiki/Chorus_(audio_effect))-like video effect built using Python and OpenCV.

It takes your webcam's input, then breaks out the Red, Green, and Blue (RGB) channels.
The Green channel is left alone, while the Red channel is delayed by a number of frames (`red_max_frames`),
and the Blue channel is delayed by a multiple of that number of frames (`delay_ratio`).

In `--interactive` mode, several variables can be manipulated via sliders ("trackbars" in OpenCV.)
In addition to delay time and delay ratio, users can tweak the parameters of a modulation effect -
basically a sine wave that the delay time is multiplied by.
Both the rate and depth of this modulation (the sine wave) can be edited live via the faders.

Note that, at a modulation depth of zero, the user manually controls the delay time.
For non-zero mod depth, the modulated delay time is computed as
`(sin(phase)+1)/2 * (mod_depth/100) * delay_length`.
So, a mod depth of 50 and a delay length of 20 means the delay time will oscillate from 0 to 10.

Optionally, users can record their session by passing a file path to  the `-o`/`--out` option.
This does not currently allow recording the interactive faders, only the resulting video.

By default, output to monitor is mirrored and output written to a file is not.
These behaviors can be inverted with te `-m` and `-f` flags, respectively.

## Setup
```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
```

## Usage
```
$ ./vidrato.py -h
usage: vidrato.py [-h] [-i] [-m] [-f] [-o OUT] [-l DELAY_LENGTH]
                  [-x DELAY_MULTIPLE] [-s MOD_SPEED]
                  [-d MOD_DEPTH]

Chorus for your video

options:
  -h, --help            show this help message and exit
  -i, --interactive     enable trackbars
  -m, --no-mirror-monitor
                        don't mirror output to monitor
  -f, --mirror-to-file  mirror output to file
  -o OUT, --out OUT     Path to output file. Only mp4 supported
                        at present.
  -l DELAY_LENGTH, --delay-length DELAY_LENGTH
                        number of frames to delay by
  -x DELAY_MULTIPLE, --delay-multiple DELAY_MULTIPLE
                        blue_length = red_length *
                        delay_multiple. Must be > 0.
  -s MOD_SPEED, --mod-speed MOD_SPEED
                        rate of modulation effect
  -d MOD_DEPTH, --mod-depth MOD_DEPTH
                        depth of modulation effect (by default,
                        0, hence off)

Made w/ <3 @ RC
```
