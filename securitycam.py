import gpiozero
import time
import picamera
import argparse
import threading
import queue
import pyaudio
import wave
import subprocess
import os
import contextlib



class AudioRecorder:
    def __init__(self, deviceIndex=0, debug=False):
        self.fn = ""            #this gets reset by the startRecording method

        self.format = pyaudio.paInt16   #16bit recording
        self.channels = 1               #1 channel
        self.sampleRate = 44100         #44kHz sample rate
        self.chunk = 4096               #2 raised to 12 samples
        self.deviceIndex = deviceIndex  #USB PnP index - not yet implemented, just uses default for now

        self.frames = []                #init the recorded frames

        self.audio = 0                  #audio object - init on recording
        self.stream = 0                 #stream - init on recording

        self.recordingNow = False       #recording flag

        self.debug=debug


    def __startRecordingThread(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format, rate=self.sampleRate,
                                        channels=self.channels,
                                        input=True, frames_per_buffer=self.chunk)

        self.recordingNow = True

        if(self.debug):
            print("DEBUG-> Starting audio recording")

        self.frames = []

        while True:
            if(self.recordingNow):
                data = self.stream.read(self.chunk, exception_on_overflow = False)
                self.frames.append(data)
            else:
                break

        #recording has stopped so save the stream
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        self.wavefile = wave.open(self.fn, 'wb')
        self.wavefile.setnchannels(self.channels)
        self.wavefile.setsampwidth(self.audio.get_sample_size(self.format))
        self.wavefile.setframerate(self.sampleRate)
        self.wavefile.writeframes(b''.join(self.frames))
        self.wavefile.close()
        #self.thr.stop()             #kill the recording thread first, then save the file...

    def startRecording(self, fn):
        if(self.debug):
            print("DEBUG-> About to start audio recording...")
        self.fn = fn
        self.thr = threading.Thread(target=self.__startRecordingThread)
        self.thr.start()

    def stopRecording(self):
        if(self.debug):
            print("DEBUG-> Stopping audio recording")
        self.recordingNow = False





class VideoRecorder:
    def __init__(self, resX=640, resY=480, debug=False, vflip=False):
        self.cam = picamera.PiCamera()
        self.cam.resolution = (resX, resY)
        
        if(vflip == True):
            self.cam.vflip = True
        
        self.fn = ""
        self.recordingNow = False
        self.debug = debug
        
    def __startRecordingThread(self):
        self.cam.start_recording(self.fn)

    def startRecording(self, fn):
        if(self.debug):
            print("DEBUG-> Video recording starting")
        self.fn = fn
        self.thr = threading.Thread(target=self.__startRecordingThread)
        self.thr.start()
        self.recordingNow = True

    def stopRecording(self):
        if(self.debug):
            print("DEBUG-> Video recording stopping")
        self.cam.stop_recording()
        self.recordingNow = False
        #self.thr.stop()


class Recorder:
    def __init__(self, resX=640, resY=480, windowLength=10, filenamePrefix='vid', video=True, audio=False, debug=False, vflip=False):
        self.pir = gpiozero.MotionSensor(4)     #motion sensor, assume we are on GPIO 4

        self.windowLength = windowLength
        self.recordingNow = False
        self.vidCount = 0
        self.windowStartTime = 0
        self.filenamePrefix = filenamePrefix
        self.fn = ""    #filename will be set when we start recording

        self.video = video
        self.audio = audio
        self.debug=debug
        self.vflip = vflip

        if(video):
            self.vr = VideoRecorder(resX, resY, self.debug, self.vflip)
        if(audio):
            self.ar = AudioRecorder(0, self.debug)

    def __recordOn(self):
        if(self.debug):
            print("DEBUG-> Record ON")
        if(self.recordingNow == False):
            self.recordingNow = True
            self.windowStartTime = time.time()

            #set the filename and start the recording also increment the counter
            self.fn = self.filenamePrefix + str(self.vidCount)

            if(self.video):
                filename = self.fn + ".h264"
                self.vr.startRecording(filename)
            if(self.audio):
                filename = self.fn + ".wav"
                self.ar.startRecording(filename)

            self.vidCount += 1
            if(self.debug):
                if(self.debug):
                    print("DEBUG-> Starting to record to a new file")

        else:
            #recording must have already started, just reset the windowBuffer
            self.windowStartTime = time.time()
            if(self.debug):
                if(self.debug):
                    print("DEBUG-> Already recording but asked to record, continuing to record, resetting buffer window")

    def __recordWindowCheck(self):
        #if recording now, check we should be or if the window has elapsed
        if(self.recordingNow):
            timeDiff = time.time() - self.windowStartTime
            if(timeDiff > self.windowLength):
                #outside of the window length, if there's no motion stop the recording
                #if there is motion right now, just carry on recording to the same file
                if(self.pir.motion_detected == False):
                    self.recordingNow = False

                    if(self.video):
                        self.vr.stopRecording()
                    if(self.audio):
                        self.ar.stopRecording()

                    if(self.video and self.audio):
                        self.__muxVideo()

                    if(self.debug):
                        print("DEBUG-> Exceded the window, stopping the recording now")

    def __clearUp(self):
        if(self.debug):
            print("DEBUG-> Clearing up")
            
        recordingFlag = False

        if(self.video):
            if(self.vr.recordingNow):
                self.vr.stopRecording()
                recordingFlag = True
        if(self.audio):
            if(self.ar.recordingNow):
                self.ar.stopRecording()
                recordingFlag = True

        if(self.audio and self.video):
            if(recordingFlag):
                self.__muxVideo()

    def __muxVideo(self):
        if(self.debug):
            print("DEBUG-> Muxing video now")
        #create a new process to mux the video and audio into an mkv file and delete the individual files
        filename = self.fn + '.mkv'
        audioFilename = self.fn + '.wav'
        videoFilename = self.fn + '.h264'
        subprocess.call(["ffmpeg", "-y", "-i", audioFilename,  "-r", "30", "-i", videoFilename,  "-filter:a", "aresample=async=1", "-c:a", "flac", "-c:v", "copy", filename])
        os.remove(audioFilename)
        os.remove(videoFilename)

    #logic loop when using a PIR to start recording
    def startPIRLoop(self):
        try:
            self.pir.when_motion = self.__recordOn
            while True:
                if(not self.pir.motion_detected): 
                    self.__recordWindowCheck()
        except KeyboardInterrupt:
            print("Stopping recording...")
            self.__clearUp()
            print("Exiting now")
            exit()


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="Enable printing messages to explain what's going on", action="store_true")
parser.add_argument("-a", "--audio", help="Enable recording audio", action="store_true")
parser.add_argument("-v", "--video", help="Enable video recording", action="store_true")
parser.add_argument("-w", "--window", help="Provide the recording window length in seconds (minimum recording length)", type=int)
parser.add_argument("-f", "--filename", help="Filename prefix for saving video/audio in current directory")
parser.add_argument("-vf", "--vflip", help="Apply a vertical flip to the camera image if it is upside down", action="store_true")

args = parser.parse_args()


debug = False
window = 10
audio = False
video = False
filename = "capture"
vflip = False

if(args.debug):
    debug = True
if(args.audio):
    audio = True
if(args.video):
    video = True
if(args.window):
    window = args.window
if(args.filename):
    filename = args.filename
if(args.vflip):
    vflip = True

if(not video and not audio):
    print('You need to record something! Try -h for options.')
    exit(1)

print("Motion sensor capture starting...")

try:
    myRecorder = Recorder(640, 480, window, filename, video, audio, debug, vflip)
    myRecorder.startPIRLoop()
finally:
    print("Byeee")
