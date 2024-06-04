import os
import json
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

def load_preferences():
    try:
        with open('laser_preferences.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_preferences(preferences):
    with open('laser_preferences.json', 'w') as f:
        json.dump(preferences, f)

audio_folder = './audio'
preferences = load_preferences()
last_choice_index = None  # Zmienna do przechowywania indeksu ostatniego wyboru

while True:
    clear_screen()
    wav_files = [f for f in os.listdir(audio_folder) if f.endswith('.wav')]
    choices = [('Change laser settings for a file', 'change_laser_settings')]
    for i, f in enumerate(wav_files):  # Używamy enumerate, aby mieć indeks
        file_path = os.path.join(audio_folder, f)
        duration = get_wav_length(file_path)
        formatted_duration = format_duration(duration)
        laser_option = preferences.get(f[:-4], False)
        display_text = f"{f[:-4]} {formatted_duration}"
        if laser_option:
            display_text += " - Distance mode"
        choices.append((display_text, f[:-4]))
    choices.append(('Exit', 'Exit'))

    default_choice = choices[last_choice_index][1] if last_choice_index is not None else None

    questions = [inquirer.List('choice', message="Select option:", choices=choices, default=default_choice)]
    answer = inquirer.prompt(questions, theme=GreenPassion())
    selected_choice = answer['choice']

    # Aktualizacja last_choice_index na podstawie aktualnego wyboru
    last_choice_index = next((i for i, choice in enumerate(choices) if choice[1] == selected_choice), None)

    if selected_choice == 'Exit':
        break
    elif selected_choice == 'change_laser_settings':
        clear_screen()
        file_choices = [(f"{f[:-4]} - Distance mode" if preferences.get(f[:-4], False) else f"{f[:-4]}", f[:-4]) for f in wav_files]
        file_question = [inquirer.List('file', message="Select file to change laser settings:", choices=file_choices)]
        file_answer = inquirer.prompt(file_question)
        laser_question = [inquirer.Confirm('laser_off', message="Enable 'Distance mode' for this file?")]
        laser_answer = inquirer.prompt(laser_question)
        if laser_answer['laser_off']:
            preferences[file_answer['file']] = True
        else:
            preferences.pop(file_answer['file'], None)
        save_preferences(preferences)
        continue

    enable_laser_off = preferences.get(selected_choice, False)

    selected_file_path = os.path.abspath(os.path.join(audio_folder, selected_choice + '.wav'))
    play_oscilloscope_music(selected_file_path, enable_laser_off)