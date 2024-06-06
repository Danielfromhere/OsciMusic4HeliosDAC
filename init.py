import os
import inquirer
from inquirer.themes import GreenPassion
import wave
import contextlib

from player import play_oscilloscope_music

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_wav_length(file_path):
    with contextlib.closing(wave.open(file_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return duration

def format_duration(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

audio_folder = './audio'

while True:
    clear_screen()
    wav_files = [f for f in os.listdir(audio_folder) if f.endswith('.wav')]
    choices = [(f"{f[:-4]} {format_duration(get_wav_length(os.path.join(audio_folder, f)))}", f[:-4]) for f in wav_files]
    choices.append(('Exit', 'Exit'))

    questions = [inquirer.List('choice', message="Select option:", choices=choices, default=None)]
    answer = inquirer.prompt(questions, theme=GreenPassion())
    selected_choice = answer['choice']

    if selected_choice == 'Exit':
        break

    selected_file_path = os.path.abspath(os.path.join(audio_folder, selected_choice + '.wav'))
    play_oscilloscope_music(selected_file_path)