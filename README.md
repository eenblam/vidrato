# Vidrato
Vidrato is a [chorus](https://en.wikipedia.org/wiki/Chorus_(audio_effect))-like video effect built using Python and OpenCV.

It takes your webcam's input, then breaks out the Red, Green, and Blue (RGB) channels.
The Green channel is left alone, while the Red channel is delayed by a number of frames (`red_max_frames`),
and the Blue channel is delayed by a multiple of that number of frames (`delay_ratio`).

In `--interactive` mode, several variables can be manipulated via sliders ("trackbars" in OpenCV.)
In addition to delay time and delay ratio, users can tweak the parameters of a modulation effect -
basically a sine wave that the delay time is multiplied by.
Both the rate and depth of this modulation (the sine wave) can be edited live via the faders.

Optionally, users can record their session by passing a file path to  the `-o`/`--out` option.
This does not currently allow recording the interactive faders, only the resulting video.

## Setup
```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
```

## Usage
```
$ ./vidrato.py -h
usage: Vidrato [-h] [-i] [-m] [-f] [-o OUT]

Chorus for your video

options:
  -h, --help            show this help message and exit
  -i, --interactive     enable trackbars
  -m, --no-mirror-monitor
                        don't mirror output to monitor
  -f, --mirror-to-file  mirror output to file
  -o OUT, --out OUT     Path to output file. Only mp4 supported at present.

Made w/ <3 @ RC
```
