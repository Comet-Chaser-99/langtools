import math
from dataclasses import replace

import numpy as np
import pytest

from langtools_praat.analysis.contracts import (
    AnalysisRequest,
    ChannelPolicy,
    IntensitySettings,
    SpectrogramSettings,
    TimeRange,
    accept,
)
from langtools_praat.analysis.intensity import (
    SILENCE_DB,
    Averaging,
    average,
    bessel_i0,
    kaiser_window,
    to_intensity,
)
from langtools_praat.errors import InvalidInput
from langtools_praat.model.sound import Sound
from langtools_praat.model.time import SampledAxis

FS = 22050
SIX_DB = 20.0 * math.log10(2.0)  # amplitude doubling, about 6.0206 dB


# ---------------------------------------------------------------------------
# Builders


def _sound(samples, rate=FS):
    values = np.atleast_2d(np.asarray(samples, dtype=np.float64))
    return Sound("x", SampledAxis.recording(values.shape[1], rate), values)


def _sine(freq, amplitude=0.1, n=FS, rate=FS, phase=0.0):
    t = (np.arange(n) + 0.5) / rate
    return amplitude * np.sin(2 * np.pi * freq * t + phase)


def _request(sound, settings=None, time_range=None, channels=None):
    return AnalysisRequest(
        source_id=sound.id,
        revision=sound.revision,
        settings=IntensitySettings() if settings is None else settings,
        time_range=(
            TimeRange(sound.axis.xmin, sound.axis.xmax) if time_range is None else time_range
        ),
        channels=ChannelPolicy.single(0) if channels is None else channels,
    )


def _intensity(sound, **kwargs):
    return to_intensity(sound, _request(sound, **kwargs))


def _db(power_pa2):
    return 10.0 * math.log10(power_pa2 / 4.0e-10)


def _interior(result, margin=2):
    return result.values[margin:-margin]


# ---------------------------------------------------------------------------
# Window and grid


def test_bessel_i0_matches_numpy_within_published_accuracy():
    x = np.linspace(0.0, 25.0, 2501)
    assert np.max(np.abs(bessel_i0(x) / np.i0(x) - 1.0)) < 2e-7
    assert bessel_i0(np.array([-2.0]))[0] == pytest.approx(bessel_i0(np.array([2.0]))[0])


def test_kaiser_window_is_symmetric_and_peaks_at_centre():
    w = kaiser_window(100, 1.0 / FS, 100.5 / FS)
    assert w.size == 201
    assert np.allclose(w, w[::-1], rtol=0.0, atol=0.0)
    assert int(np.argmax(w)) == 100
    assert w[100] == pytest.approx(bessel_i0(np.array([2 * math.pi**2 + 0.5]))[0])
    assert w[0] / w[100] < 1e-6


def test_default_time_step_is_quarter_of_logical_window():
    result = _intensity(_sound(_sine(440.0)), settings=IntensitySettings(pitch_floor=100.0))
    assert result.time.dx == pytest.approx(0.008)


def test_frame_count_and_centring_follow_short_term_rule():
    sound = _sound(_sine(440.0, n=FS))
    result = _intensity(sound)
    duration = sound.axis.nx * sound.axis.dx
    physical = 6.4 / 100.0
    assert result.time.nx == math.floor((duration - physical) / result.time.dx) + 1
    first = result.time.x1
    last = first + (result.time.nx - 1) * result.time.dx
    middle = sound.axis.x1 - 0.5 * sound.axis.dx + 0.5 * duration
    assert 0.5 * (first + last) == pytest.approx(middle, abs=1e-12)


def test_explicit_time_step_is_used():
    result = _intensity(
        _sound(_sine(440.0)), settings=IntensitySettings(pitch_floor=100.0, time_step=0.005)
    )
    assert result.time.dx == 0.005


def test_rejects_sound_shorter_than_physical_window():
    sound = _sound(_sine(440.0, n=int(0.06 * FS)))
    with pytest.raises(InvalidInput):
        _intensity(sound)


def test_shortest_accepted_sound_gives_one_frame():
    sound = _sound(_sine(440.0, n=math.ceil(0.064 * FS) + 1))
    assert _intensity(sound).time.nx == 1


# Reference arithmetic order (pinned Praat 56ed24ef, fon/Sound_to_Intensity.cpp L54-L65 and
# fon/Sampled.cpp L74-L77): logical = 3.2 * (1 / pf), step = logical / 4, physical = 2 * logical.
# At these settings 6.4 / pf and 0.8 / pf differ from that in the last bit, which changes the
# discrete results below (PR #29 review).


def test_sound_of_exactly_6_4_over_pitch_floor_is_rejected_in_reference_order():
    # 0.16 s, equal to 6.4 / 40 in exact arithmetic
    sound = _sound(_sine(440.0, n=1280, rate=8000), rate=8000)
    with pytest.raises(InvalidInput):
        _intensity(sound, settings=IntensitySettings(pitch_floor=40.0))


def test_frame_count_uses_reference_order_window_and_step():
    sound = _sound(_sine(440.0, n=1600, rate=8000), rate=8000)  # 0.2 s
    result = _intensity(sound, settings=IntensitySettings(pitch_floor=40.0))
    assert result.time.nx == 2  # 6.4/pf and 0.8/pf would give 3


def test_half_window_samples_use_reference_order(monkeypatch):
    from langtools_praat.analysis import intensity as module

    seen = []
    original = module.kaiser_window

    def spy(half_samples, dx, half_duration):
        seen.append(half_samples)
        return original(half_samples, dx, half_duration)

    monkeypatch.setattr(module, "kaiser_window", spy)
    sound = _sound(_sine(440.0, n=11025, rate=11025), rate=11025)
    _intensity(sound, settings=IntensitySettings(pitch_floor=49.0))
    assert seen == [719]  # 6.4/pf would give 720


def test_rejects_wrong_request_kind_and_stale_revision():
    sound = _sound(_sine(440.0))
    with pytest.raises(InvalidInput):
        to_intensity(sound, _request(sound, settings=SpectrogramSettings()))
    stale = replace(_request(sound), revision=sound.revision + 1)
    with pytest.raises(InvalidInput):
        to_intensity(sound, stale)


def test_time_range_limits_the_analysis_to_the_part():
    sound = _sound(_sine(440.0, n=2 * FS))
    result = _intensity(sound, time_range=TimeRange(0.5, 1.5))
    assert result.time.xmin == 0.5 and result.time.xmax == 1.5
    assert result.time.x1 - 0.032 >= 0.5 - 1e-9
    assert result.time.x1 + (result.time.nx - 1) * result.time.dx + 0.032 <= 1.5 + 1e-9


def test_result_is_immutable_and_carries_its_request():
    sound = _sound(_sine(440.0))
    request = _request(sound)
    result = to_intensity(sound, request)
    assert not result.values.flags.writeable
    assert result.provenance.request is request
    assert accept(result, sound.id, sound.revision, request.token)


# ---------------------------------------------------------------------------
# Scientific cases (spec §17: DC, silence, doubling, stereo)


@pytest.mark.parametrize("freq", [220.0, 440.0, 1000.0])
def test_sine_gives_its_mean_square_in_db(freq):
    amplitude = 0.1
    result = _intensity(_sound(_sine(freq, amplitude)))
    expected = _db(amplitude**2 / 2.0)
    assert np.max(np.abs(_interior(result) - expected)) < 0.01


def test_amplitude_doubling_adds_six_db():
    signal = _sine(440.0) + 0.3 * _sine(1300.0)
    base = _intensity(_sound(signal)).values
    doubled = _intensity(_sound(2.0 * signal)).values
    assert np.allclose(doubled - base, SIX_DB, rtol=0.0, atol=1e-9)


def test_dc_offset_is_removed_by_local_mean_subtraction():
    signal = _sine(440.0)
    plain = _intensity(_sound(signal)).values
    offset = _intensity(_sound(signal + 0.5)).values
    assert np.allclose(offset, plain, rtol=0.0, atol=1e-6)


def test_dc_offset_counts_as_energy_without_mean_subtraction():
    settings = IntensitySettings(subtract_mean=False)
    result = _intensity(_sound(np.full(FS, 0.2)), settings=settings)
    assert np.allclose(result.values, _db(0.04), rtol=0.0, atol=1e-9)
    centred = _intensity(_sound(np.full(FS, 0.2)))
    assert np.all(centred.values < -200.0)  # only rounding residue is left


def test_silence_is_minus_300_db_and_defined():
    result = _intensity(_sound(np.zeros(FS)))
    assert np.all(result.values == SILENCE_DB)
    assert result.valid.all()
    for method in Averaging:
        assert average(result, method) == pytest.approx(SILENCE_DB)


def test_unequal_stereo_channels_combined_pool_their_energies():
    left, right = _sine(440.0, 0.1), _sine(660.0, 0.03)
    combined = _intensity(_sound([left, right]), channels=ChannelPolicy.combined())
    one = _intensity(_sound([left, right]), channels=ChannelPolicy.single(0))
    two = _intensity(_sound([left, right]), channels=ChannelPolicy.single(1))
    pooled = 10.0 * np.log10((10.0 ** (one.values / 10) + 10.0 ** (two.values / 10)) / 2.0)
    assert np.allclose(combined.values, pooled, rtol=0.0, atol=1e-9)
    assert np.allclose(one.values, _intensity(_sound(left)).values, rtol=0.0, atol=0.0)


def test_identical_stereo_channels_combined_match_mono():
    signal = _sine(440.0)
    stereo = _intensity(_sound([signal, signal]), channels=ChannelPolicy.combined())
    assert np.allclose(stereo.values, _intensity(_sound(signal)).values, rtol=0.0, atol=1e-9)


def test_edge_frames_with_clipped_windows_stay_close_to_interior():
    # A 0.03 s time step lets the first/last windows hang over the sound's edges.
    sound = _sound(_sine(440.0, n=int(0.2 * FS)))
    result = _intensity(sound, settings=IntensitySettings(time_step=0.001))
    assert np.isfinite(result.values).all()
    assert np.max(np.abs(result.values - _db(0.01 / 2.0))) < 0.05


# ---------------------------------------------------------------------------
# Averaging queries


def _contour(values, dx=0.01, x1=0.035, xmin=0.0, xmax=None):
    """An Intensity with the given frame values on a regular grid."""
    sound = _sound(_sine(440.0))
    base = _intensity(sound)
    n = len(values)
    xmax = x1 + (n - 1) * dx + 0.035 if xmax is None else xmax
    axis = SampledAxis(xmin, xmax, n, dx, x1)
    request = replace(base.provenance.request, time_range=TimeRange(xmin, xmax))
    provenance = replace(base.provenance, request=request)
    return type(base)(provenance, axis, np.asarray(values, dtype=np.float64))


def test_constant_contour_has_that_value_for_every_method():
    result = _contour([70.0] * 9)
    for method in Averaging:
        assert average(result, method) == pytest.approx(70.0)


def test_averaging_methods_differ_as_defined():
    result = _contour([60.0] * 5 + [80.0] * 5)
    by_db = average(result, Averaging.DB)
    by_energy = average(result, Averaging.ENERGY)
    by_sones = average(result, Averaging.SONES)
    assert by_db == pytest.approx(70.0)
    assert by_energy == pytest.approx(10.0 * math.log10((1e6 + 1e8) / 2.0))
    assert by_sones == pytest.approx(10.0 * math.log2((2.0**6 + 2.0**8) / 2.0))
    assert by_db < by_sones < by_energy


def test_whole_object_mean_is_plain_frame_mean_in_each_unit():
    rng = np.random.default_rng(0)
    values = rng.normal(65.0, 8.0, 40)
    result = _contour(values)
    assert average(result, Averaging.DB) == pytest.approx(float(values.mean()))
    energy = 10.0 * math.log10(float(np.mean(10.0 ** (values / 10.0))))
    assert average(result, Averaging.ENERGY) == pytest.approx(energy)
    assert average(result, Averaging.DB, (0.3, 0.3)) == pytest.approx(float(values.mean()))


@pytest.mark.parametrize("window", [(0.05, 0.12), (0.061, 0.0612), (0.04, 0.2), (0.1, 0.105)])
def test_db_mean_of_a_linear_ramp_is_its_value_at_the_window_middle(window):
    dx, x1 = 0.01, 0.035
    values = 50.0 + 100.0 * (x1 + np.arange(30) * dx)  # 100 dB/s ramp
    result = _contour(values, dx=dx, x1=x1)
    middle = 0.5 * (window[0] + window[1])
    assert average(result, Averaging.DB, window) == pytest.approx(50.0 + 100.0 * middle)


def test_values_are_held_for_half_a_step_beyond_the_end_frames():
    values = [60.0, 70.0, 80.0]
    result = _contour(values, dx=0.01, x1=0.035)
    # [x1 - dx/2, x1]: constant 60, then the ramp 60 -> 70 over [x1, x1 + dx].
    expected = (0.005 * 60.0 + 0.01 * 65.0) / 0.015
    assert average(result, Averaging.DB, (0.0, 0.045)) == pytest.approx(expected)


def test_undefined_frames_are_skipped():
    values = np.array([60.0, np.nan, 80.0, 80.0, np.nan, np.nan, 70.0])
    result = _contour(values)
    assert math.isfinite(average(result, Averaging.DB))
    assert average(result, Averaging.MEDIAN) == pytest.approx(75.0)
    only = _contour([np.nan, 70.0, np.nan])
    assert average(only, Averaging.DB) == pytest.approx(70.0)
    assert average(only, Averaging.ENERGY) == pytest.approx(70.0)


def test_all_undefined_or_outside_range_is_nan():
    assert math.isnan(average(_contour([np.nan] * 4), Averaging.ENERGY))
    assert math.isnan(average(_contour([np.nan] * 4), Averaging.MEDIAN))
    result = _contour([60.0, 70.0])
    assert math.isnan(average(result, Averaging.DB, (5.0, 6.0)))
    with pytest.raises(InvalidInput):
        average(result, Averaging.DB, (math.nan, 1.0))


@pytest.mark.parametrize(
    ("values", "median"), [([3.0, 1.0, 2.0], 2.0), ([4.0, 1.0, 3.0, 2.0], 2.5), ([5.0], 5.0)]
)
def test_median_of_frames(values, median):
    assert average(_contour(values), Averaging.MEDIAN) == pytest.approx(median)


def test_median_uses_frames_inside_the_range():
    result = _contour([10.0, 20.0, 30.0, 40.0, 50.0], dx=0.01, x1=0.035)
    assert average(result, Averaging.MEDIAN, (0.04, 0.07)) == pytest.approx(30.0)


def test_energy_mean_of_stationary_sine_matches_its_spl():
    amplitude = 0.05
    result = _intensity(_sound(_sine(500.0, amplitude, n=2 * FS)))
    assert average(result, Averaging.ENERGY) == pytest.approx(_db(amplitude**2 / 2), abs=0.01)
