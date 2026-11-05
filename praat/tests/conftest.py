import os

import numpy as np
import pytest
import soundfile as sf

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def wav(tmp_path):
    path = tmp_path / "voz con ɲ.wav"
    values = np.zeros((16000, 2))
    values[11, 0], values[12000, 1] = 0.75, -0.5
    sf.write(path, values, 16000, subtype="PCM_16")
    return path
