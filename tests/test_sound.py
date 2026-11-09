from unittest.mock import Mock

import numpy as np
import pytest

from timeline_kun import sound


@pytest.fixture
def audio(monkeypatch):
    data = np.array([[0.25], [-0.5], [0.75]], dtype="float32")
    monkeypatch.setattr(sound.sf, "read", Mock(return_value=(data, 48000)))
    output = Mock()
    monkeypatch.setattr(sound.sd, "OutputStream", output)
    return sound.AudioPlayer(), data, output


@pytest.mark.parametrize("idle_seconds", [10, 120])
def test_playback_after_idle_uses_active_output(audio, idle_seconds):
    player, data, output = audio
    player.prepare("test.wav")
    callback = output.call_args.kwargs["callback"]
    buffer = np.empty((4800, 1), dtype="float32")

    for _ in range(2):
        # Simulate the device consuming silence throughout the event.
        for _ in range(idle_seconds * 10):
            buffer.fill(1)
            callback(buffer, len(buffer), None, None)
            assert not buffer.any()
        player.play_sound("test.wav")
        callback(buffer, len(buffer), None, None)
        np.testing.assert_array_equal(buffer[:len(data)], data)
        assert not buffer[len(data):].any()

    output.assert_called_once()
    output.return_value.start.assert_called_once()
    output.return_value.close.assert_not_called()
    sound.sf.read.assert_called_once()


def test_audio_continues_across_blocks_and_restarts_on_request(audio):
    player, data, output = audio
    player.play_sound("test.wav")
    callback = output.call_args.kwargs["callback"]
    buffer = np.empty((2, 1), dtype="float32")
    callback(buffer, 2, None, None)
    np.testing.assert_array_equal(buffer, data[:2])
    callback(buffer, 2, None, None)
    np.testing.assert_array_equal(buffer[:, 0], [0.75, 0])
    player.play_sound("test.wav")
    callback(buffer, 2, None, None)
    np.testing.assert_array_equal(buffer, data[:2])


def test_close_releases_output_and_discards_playback(audio):
    player, _, output = audio
    player.play_sound("test.wav")
    player.close()
    player.close()
    output.return_value.abort.assert_called_once()
    output.return_value.close.assert_called_once()
    assert player._playback is None


def test_failed_start_releases_output(audio):
    player, _, output = audio
    output.return_value.start.side_effect = RuntimeError("Device unavailable")
    with pytest.raises(RuntimeError, match="Device unavailable"):
        player.prepare("test.wav")
    output.return_value.close.assert_called_once()
    assert player._stream is None
