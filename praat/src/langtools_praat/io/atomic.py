import os
import tempfile
from pathlib import Path


def save_bytes(path: Path, data: bytes, *, overwrite: bool = False) -> None:
    """Same-directory temporary write; failure leaves the previous target intact.

    A hard-link publication gives no-clobber semantics for new paths. Replacement
    uses os.replace only when the caller explicitly allows overwrite.
    """
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
