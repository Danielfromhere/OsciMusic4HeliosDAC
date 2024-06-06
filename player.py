import wave
import numpy as np
import ctypes
import msvcrt
import pyaudio

class HeliosPoint(ctypes.Structure):
    _fields_ = [('x', ctypes.c_uint16),
                ('y', ctypes.c_uint16),
                ('r', ctypes.c_uint8),
                ('g', ctypes.c_uint8),
                ('b', ctypes.c_uint8),
                ('i', ctypes.c_uint8)]

def to_12bit(value):
    return max(0, min(4095, int((value + 32768) * 4095 / 65535)))

def play_oscilloscope_music(file_path):
    print('Visualization in progress, press x to stop')
    with wave.open(file_path, 'r') as wav_file:
        frame_rate = wav_file.getframerate()
        n_channels, sampwidth = wav_file.getnchannels(), wav_file.getsampwidth()
        frames = wav_file.readframes(-1)
        samples = np.frombuffer(frames, dtype=np.int16)
        samples = np.reshape(samples, (-1, n_channels))

    batch_size = 4096
    frameType = HeliosPoint * batch_size

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(sampwidth),
                    channels=n_channels,
                    frames_per_buffer=batch_size,
                    rate=frame_rate,
                    output=True)

    HeliosLib = ctypes.cdll.LoadLibrary("./HeliosLaserDAC.dll")
    numDevices = HeliosLib.OpenDevices()

    for i in range(0, len(samples), batch_size):
        frame = frameType()
        audio_frame = samples[i:i+batch_size]

        for j in range(len(audio_frame)):
            x, y = to_12bit(audio_frame[j][0]), 4095 - to_12bit(audio_frame[j][1])
            frame[j] = HeliosPoint(x, y, 255, 255, 255, 0)

        for j in range(numDevices):
            HeliosLib.SetShutter(j, True)
            while HeliosLib.GetStatus(j) == 0:
                pass

            HeliosLib.WriteFrame(j, ctypes.c_uint(frame_rate), ctypes.c_ubyte(0), ctypes.pointer(frame), ctypes.c_uint(len(audio_frame)))

        stream.write(audio_frame.tobytes())

        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'x':
                break
            elif key == b' ':
                while True:
                    if msvcrt.kbhit() and msvcrt.getch() == b' ':
                        break

    stream.stop_stream()
    stream.close()
    p.terminate()
    HeliosLib.CloseDevices()