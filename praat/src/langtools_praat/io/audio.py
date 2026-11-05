"""Bounded WAV adapter. Reading/plotting never requires decoding the entire file."""

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from uuid import uuid4

import numpy as np
import soundfile as sf
from numpy.typing import NDArray

from ..errors import Cancelled, InvalidInput, StaleRevision
from ..model.sound import Sound, immutable_samples
from ..model.time import SampledAxis

SUBTYPES = {"PCM_16": 16, "PCM_24": 24, "PCM_32": 32}


def signature(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


@dataclass(frozen=True)
class AudioFile:
    path: Path
    name: str
    axis: SampledAxis
    channels: int
    subtype: str
    fingerprint: tuple[int, int, int, int]
    id: str = field(default_factory=lambda: str(uuid4()))
    revision: int = 0
    kind: str = field(default="Sound", init=False)

    @classmethod
    def open(cls, path: Path, *, xmin: float = 0.0):
        path = Path(path).resolve()
        before = signature(path)
        try:
            with sf.SoundFile(path) as source:
                if source.format not in ("WAV", "WAVEX") or source.subtype not in SUBTYPES:
                    raise InvalidInput("Supported audio: WAV PCM16, PCM24 or PCM32.")
                if source.channels not in (1, 2):
                    raise InvalidInput("Only mono and stereo audio are supported.")
                axis = SampledAxis.recording(source.frames, source.samplerate, xmin)
                result = cls(path, path.stem, axis, source.channels, source.subtype, before)
        except sf.LibsndfileError as error:
            raise InvalidInput(f"Cannot decode audio: {error}") from error
        if signature(path) != before:
            raise StaleRevision("Audio file changed while opening; reopen it.")
        return result

    def describe(self) -> dict:
        return {
            "id": self.id,
            "revision": self.revision,
            "name": self.name,
            "kind": self.kind,
            "path": str(self.path),
            "channels": self.channels,
            "frames": self.axis.nx,
            "sample_rate": self.axis.sample_rate,
            "subtype": self.subtype,
            "xmin": self.axis.xmin,
            "xmax": self.axis.xmax,
            "dx": self.axis.dx,
            "x1": self.axis.x1,
        }

    def read_frames(
        self, first: int, count: int, cancellation: Event | None = None
    ) -> NDArray[np.float64]:
        if type(first) is not int or type(count) is not int or first < 0 or count < 0:
            raise InvalidInput("Frame start and count must be nonnegative integers.")
        if first + count > self.axis.nx:
            raise InvalidInput("Requested frames extend beyond the recording.")
        if cancellation is not None and cancellation.is_set():
            raise Cancelled("Audio read cancelled.")
        if signature(self.path) != self.fingerprint:
            raise StaleRevision("Audio file changed on disk; reopen it before reading.")
        try:
            with sf.SoundFile(self.path) as source:
                source.seek(first)
                values = source.read(count, dtype="float64", always_2d=True).T
        except sf.LibsndfileError as error:
            raise InvalidInput(f"Cannot read audio: {error}") from error
        if values.shape != (self.channels, count) or signature(self.path) != self.fingerprint:
            raise StaleRevision("Audio file changed during the read.")
        if cancellation is not None and cancellation.is_set():
            raise Cancelled("Audio read cancelled.")
        return immutable_samples(values)

    def load(self, *, max_bytes: int = 256 * 1024 * 1024) -> Sound:
        if self.axis.nx * self.channels * 8 > max_bytes:
            raise InvalidInput("Recording exceeds in-memory limit; use bounded frame reads.")
        return Sound(
            self.name, self.axis, self.read_frames(0, self.axis.nx), self.id, self.revision
        )


def write_wav(
    path: Path, sound: Sound, *, subtype: str = "PCM_16", overwrite: bool = False
) -> None:
    """Explicit nearest-even integer quantization, saturation, no dither/normalization.

    Reject clipping rather than silently change out-of-range input. WAV cannot retain
    a nonzero time domain; only samples and the integer sample rate are exported.
    """
    import io

    from .atomic import save_bytes

    if subtype not in SUBTYPES:
        raise InvalidInput("Output subtype must be PCM_16, PCM_24 or PCM_32.")
    rate = round(sound.axis.sample_rate)
    if abs(rate - sound.axis.sample_rate) > 1e-6:
        raise InvalidInput("WAV export needs an integer sample rate.")
    if np.any(sound.samples < -1) or np.any(sound.samples > 1):
        raise InvalidInput("Audio would clip; explicitly scale it before exporting.")
    bits = SUBTYPES[subtype]
    scale = 2 ** (bits - 1)
    quantized = np.clip(np.rint(sound.samples * scale), -scale, scale - 1).astype(np.int64)
    left_aligned = (quantized.T * (2 ** (32 - bits))).astype(np.int32)
    buffer = io.BytesIO()
    sf.write(buffer, left_aligned, rate, format="WAV", subtype=subtype)
    save_bytes(Path(path), buffer.getvalue(), overwrite=overwrite)
