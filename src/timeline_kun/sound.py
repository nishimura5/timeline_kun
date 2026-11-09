import os
import sys
import threading

import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """
    A simple class for playing WAV audio files at specified timings
    """

    def __init__(self):
        """Initialize the audio player"""
        self.audio_cache = {}  # Cache for loaded audio data
        self._stream = None
        self._format = None
        self._playback = None
        self._lock = threading.Lock()

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
            data, samplerate = sf.read(sound_path, dtype="float32", always_2d=True)
            self.audio_cache[sound_path] = (data, samplerate)
        return self.audio_cache[sound_path]

    def prepare(self, sound_name):
        """Keep the output active, including during long silent intervals."""
        data, samplerate = self.load_audio(sound_name)
        audio_format = (samplerate, data.shape[1])
        if self._stream is None or self._format != audio_format:
            self.close()
            stream = sd.OutputStream(
                samplerate=samplerate,
                channels=data.shape[1],
                dtype="float32",
                latency="low",
                callback=self._render,
            )
            try:
                stream.start()
            except Exception:
                stream.close()
                raise
            self._stream = stream
            self._format = audio_format
        return data

    def _render(self, outdata, frames, time_info, status):
        outdata.fill(0)
        # Never block the audio callback while the GUI changes playback.
        if not self._lock.acquire(blocking=False):
            return
        try:
            if self._playback is None:
                return
            data, position = self._playback
            count = min(frames, len(data) - position)
            outdata[:count] = data[position : position + count]
            position += count
            self._playback = (data, position) if position < len(data) else None
        finally:
            self._lock.release()

    def close(self):
        """Release the output device when the timer window closes."""
        if self._stream is not None:
            try:
                self._stream.abort()
            finally:
                self._stream.close()
                self._stream = None
                self._format = None
        with self._lock:
            self._playback = None

    def play_sound(self, filepath, play_time=None):
        """
        Play audio at a specified time

        Args:
            filepath (str): Path to the WAV file to play
            play_time (datetime.datetime, optional): Time to play. If None, play immediately
        """
        if play_time is None:
            data = self.prepare(filepath)
            with self._lock:
                self._playback = (data, 0)
