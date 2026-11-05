from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from ..errors import InvalidInput
from .time import SampledAxis


def immutable_samples(values: NDArray) -> NDArray[np.float64]:
    """Own a bytes-backed copy: even setflags(write=True) cannot mutate this snapshot."""
    array = np.asarray(values, dtype=np.float64)
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(array.shape)


@dataclass(frozen=True, eq=False)
class Sound:
    name: str
    axis: SampledAxis
    samples: NDArray[np.float64]
    id: str = field(default_factory=lambda: str(uuid4()))
    revision: int = 0
    kind: str = field(default="Sound", init=False)

    def __post_init__(self) -> None:
        values = np.asarray(self.samples, dtype=np.float64)
        if values.ndim != 2 or values.shape[0] not in (1, 2):
            raise InvalidInput("Samples must have shape (channels, frames), mono or stereo.")
        if values.shape[1] != self.axis.nx or not np.isfinite(values).all():
            raise InvalidInput("Samples must be finite and match the sampled axis.")
        object.__setattr__(self, "samples", immutable_samples(values))

    @property
    def channels(self) -> int:
        return self.samples.shape[0]
