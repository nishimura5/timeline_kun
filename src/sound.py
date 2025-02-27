import os
import sys

import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """
    A simple class for playing WAV audio files at specified timings
    """

    def __init__(self):
        """Initialize the audio player"""
        self.audio_cache = {}  # Cache for loaded audio data

    def load_audio(self, sound_name):
        """
        Load a WAV file and save it to cache

        Args:
            filepath (str): Path to the WAV file

        Returns:
            tuple: (audio data, sample rate)
        """
        if getattr(sys, "frozen", False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(__file__)
        sound_path = os.path.join(current_dir, "sound", sound_name)

        if sound_path not in self.audio_cache:
            data, samplerate = sf.read(sound_path)
            self.audio_cache[sound_path] = (data, samplerate)
        return self.audio_cache[sound_path]

    def play_sound(self, filepath, play_time=None):
        """
        Play audio at a specified time

        Args:
            filepath (str): Path to the WAV file to play
            play_time (datetime.datetime, optional): Time to play. If None, play immediately
        """
        # Pre-load the audio
        data, samplerate = self.load_audio(filepath)

        if play_time is None:
            # Play immediately
            sd.play(data, samplerate)
            return
