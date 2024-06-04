import wave
import numpy as np
import ctypes
import msvcrt
import pyaudio
import math

class HeliosPoint(ctypes.Structure):
    _fields_ = [('x', ctypes.c_uint16),
                ('y', ctypes.c_uint16),
                ('r', ctypes.c_uint8),
                ('g', ctypes.c_uint8),
                ('b', ctypes.c_uint8),
                ('i', ctypes.c_uint8)]

def to_12bit(value):
    return max(0, min(4095, int((value + 32768) * 4095 / 65535)))

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def play_oscilloscope_music(file_path, enable_laser_off=False):
    print('Wizualizacja w toku, nacisnij x aby przerwac')
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

    prev_x, prev_y = 0, 0  # Inicjalizacja poprzednich wartości
    change_color = False  # Zmienna pomocnicza do śledzenia, czy zmienić kolor poprzedniego punktu

    for i in range(0, len(samples), batch_size):
        frame = frameType()
        audio_frame = samples[i:i+batch_size]

        for j in range(len(audio_frame)):
            x, y = to_12bit(audio_frame[j][0]), 4095 - to_12bit(audio_frame[j][1])
            distance = calculate_distance(x, y, prev_x, prev_y) if j > 0 else 0

            if enable_laser_off and distance > 300:
                if j > 0:  # Jeśli nie jest to pierwszy punkt w partii
                    frame[j-1] = HeliosPoint(prev_x, prev_y, 0, 0, 0, 0)  # Ustaw kolor poprzedniego punktu na 0
                change_color = True  # Oznacz aktualny punkt do zmiany koloru
            else:
                change_color = False

            if change_color:
                frame[j] = HeliosPoint(x, y, 0, 0, 0, 0)  # Ustaw kolor aktualnego punktu na 0
            else:
                frame[j] = HeliosPoint(x, y, 255, 255, 255, 0)  # Domyślny kolor

            prev_x, prev_y = x, y  # Aktualizacja poprzednich wartości

        stream.write(audio_frame.tobytes())

        for j in range(numDevices):
            HeliosLib.SetShutter(j, True)
            while HeliosLib.GetStatus(j) == 0:
                pass
            HeliosLib.WriteFrame(j, ctypes.c_uint(frame_rate + 6), ctypes.c_ubyte(0), ctypes.pointer(frame), ctypes.c_uint(len(audio_frame)))

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