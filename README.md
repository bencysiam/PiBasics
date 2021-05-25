# Raspberry Pi Course

Some basic python code for the Raspberry Pi's IR motion detector, camera module and also a security camera project that records video and audio when motion is detected by a connected PIR.

# Security Camera

A project using the Raspberry Pi Camera module, PIR sensor and a USB microphone. This code is not maintained so may not work in the future. It is a rough proof of concept only. 

The code will enter a loop until you Ctrl-c to escape. When the PIR detects motion the video and audio recording window will begin or reset to zero. Whilst in the window it will be recording. If the window elapses without any motion detected, recording will stop and the files will be saved. At the end video and audio are muxed into a mkv file.

## Security Camera Requirements

You will need python3, pip and ffmpeg installed for this. This code assumes one USB microphone is connected and assumes the PIR is installed on GPIO 4.

```
sudo apt update
sudo apt upgrade -y
sudo apt install libportaudio2
sudo pip3 install pyaudio
```

## Security Camera Usage

You can get help by sending the -h switch on the command line:

```
python3 securitycam.py -h
```

The ALSA libraries throw out lots of errors, so I add ```2>/dev/null``` to re-direct stderr.

Example use recording audio and video, being verbose with debug messages, a 10 second capture window, naming all files test, e.g. test0.mkv:

```
python3 securitycam.py -a -v -d -w 10 -f test 2>/dev/null
```
