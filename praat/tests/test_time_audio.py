from dataclasses import replace
from threading import Event

import numpy as np
import pytest
import soundfile as sf

from langtools_praat.errors import Cancelled, InvalidInput, StaleRevision
from langtools_praat.io.audio import AudioFile, write_wav
from langtools_praat.media.waveform import summarize
from langtools_praat.model.sound import Sound
from langtools_praat.model.time import SampledAxis


@pytest.mark.parametrize("rate", [16000, 44100, 48000])
def test_sample_centers_and_fractional_queries(rate):
    axis = SampledAxis.recording(rate, rate)
    assert axis.xmin == 0
    assert axis.xmax == pytest.approx(1)
    assert axis.time(1) == pytest.approx(0.5 / rate)
    assert axis.time(rate) == pytest.approx(1 - 0.5 / rate)
    assert axis.sample_number(0.1) == pytest.approx(0.1 * rate + 0.5)
    assert axis.frame_range(axis.time(1), axis.time(3)) == (0, 2)
    assert axis.frame_range(-10, 20) == (0, rate)


def test_nonzero_domain_and_no_implicit_rounding():
    axis = SampledAxis.recording(10000, 10000, xmin=3.25)
    assert axis.time(1) == pytest.approx(3.25005)
    assert axis.sample_number(3.35) == pytest.approx(1000.5)
    assert axis.frame_range(3.25, 3.25) == (0, 0)
    with pytest.raises(InvalidInput):
        axis.frame_range(float("nan"), 4)


@pytest.mark.parametrize("args", [(0, 1, 0, 0.1, 0.05), (0, 1, 4, 0, 0.1), (0, 1, 10, 1, 0.5)])
def test_invalid_axis(args):
    with pytest.raises(InvalidInput):
        SampledAxis(*args)


def test_sound_owns_an_immutable_snapshot():
    original = np.zeros((2, 16))
    sound = Sound("test", SampledAxis.recording(16, 16000), original)
    original[0, 0] = 1
    assert sound.samples[0, 0] == 0
    with pytest.raises(ValueError):
        sound.samples.setflags(write=True)
    with pytest.raises(InvalidInput):
        replace(sound, samples=np.zeros((16, 2)))


def test_bounded_audio_reads_and_source_identity(wav):
    source = AudioFile.open(wav)
    assert source.describe()["channels"] == 2
    assert source.axis.nx == 16000
    block = source.read_frames(10, 3)
    assert block.shape == (2, 3)
    assert block[0, 1] == 0.75
    with pytest.raises(InvalidInput):
        source.read_frames(15999, 2)
    with pytest.raises(InvalidInput):
        source.load(max_bytes=16)
    wav.write_bytes(b"replaced")
    with pytest.raises(StaleRevision):
        source.read_frames(0, 1)


@pytest.mark.parametrize("subtype,bits", [("PCM_16", 16), ("PCM_24", 24), ("PCM_32", 32)])
def test_pcm_quantization_channels_and_round_trip(tmp_path, subtype, bits):
    # Includes ties, both endpoints, fractional values and unequal stereo channels.
    scale = 2 ** (bits - 1)
    values = np.array([[-1, -0.5, 0, 0.5 / scale, 1.5 / scale, 1], [0.25] * 6])
    sound = Sound("test", SampledAxis.recording(6, 48000), values)
    path = tmp_path / "roundtrip.wav"
    write_wav(path, sound, subtype=subtype)
    result = AudioFile.open(path).load()
    expected = np.clip(np.rint(values * scale), -scale, scale - 1) / scale
    np.testing.assert_array_equal(result.samples, expected)
    assert result.channels == 2
    assert result.axis.sample_rate == pytest.approx(48000)
    with pytest.raises(FileExistsError):
        write_wav(path, sound, subtype=subtype)


def test_reject_unsupported_and_clipping(tmp_path):
    path = tmp_path / "float.wav"
    sf.write(path, np.zeros(10), 16000, subtype="FLOAT")
    with pytest.raises(InvalidInput, match="PCM"):
        AudioFile.open(path)
    sound = Sound("loud", SampledAxis.recording(2, 16000), np.array([[1.1, -1.1]]))
    with pytest.raises(InvalidInput, match="clip"):
        write_wav(tmp_path / "output.wav", sound)
    assert not (tmp_path / "output.wav").exists()


def test_waveform_preserves_peaks_in_each_channel(wav):
    source = AudioFile.open(wav)
    first = summarize(source, 0, 1, channel=0, pixels=10)
    second = summarize(source, 0, 1, channel=1, pixels=10)
    assert len(first.times) == 10
    assert first.maximum[0] == 0.75
    assert first.minimum.min() == 0
    assert second.minimum[7] == -0.5
    assert second.maximum.max() == 0
    assert summarize(source, 0, 0).times.size == 0


def test_waveform_crosses_read_blocks_with_bounded_memory(tmp_path):
    path = tmp_path / "large.wav"
    samples = np.zeros(200000)
    samples[65535], samples[65536], samples[131071] = 0.5, -0.75, 0.25
    sf.write(path, samples, 48000, subtype="PCM_16")
    original = AudioFile.open(path)

    class RecordingSource:
        axis, channels = original.axis, original.channels
        requests = []

        def read_frames(self, first, count, cancellation):
            self.requests.append((first, count))
            return original.read_frames(first, count, cancellation)

    source = RecordingSource()
    wave = summarize(source, 0, original.axis.xmax, pixels=3)
    assert max(count for _, count in source.requests) <= 65536
    assert len(source.requests) == 4
    assert wave.maximum[0] == 0.5
    assert wave.minimum[0] == -0.75
    assert wave.maximum[1] == 0.25


def test_cancellation(wav):
    token = Event()
    token.set()
    source = AudioFile.open(wav)
    with pytest.raises(Cancelled):
        source.read_frames(0, 1, token)
    with pytest.raises(Cancelled):
        summarize(source, 0, 1, cancellation=token)
