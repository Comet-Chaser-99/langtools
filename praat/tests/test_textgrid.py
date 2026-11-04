import pytest

from langtools_praat.errors import InvalidInput
from langtools_praat.io.textgrid import Limits, dumps, loads, read, write
from langtools_praat.model.textgrid import Interval, IntervalTier, Point, PointTier, TextGrid

# Hand-authored fixtures follow the public format examples. Not produced by our writer.
MIXED = '''File type = "ooTextFile"
Object class = "TextGrid"
3.25 5.25 ! grid domain
<exists> 2
item [99]:
class = "IntervalTier" name = "phones"
3.25 5.25 intervals: size = 2
intervals [100]: xmin = 3.25 xmax = 4.0 text = "ʔa! ""hi"""
intervals [2]: 4.0 5.25 "second
line"
"TextTier" "events" 3.25 5.25 1
4.25 "\\ct"
'''


def semantic(grid):
    return (
        grid.xmin,
        grid.xmax,
        tuple(
            (
                type(t).__name__,
                t.name,
                t.xmin,
                t.xmax,
                tuple((i.xmin, i.xmax, i.label) for i in t.intervals)
                if isinstance(t, IntervalTier)
                else tuple((p.time, p.label) for p in t.points),
            )
            for t in grid.tiers
        ),
    )


def test_mixed_token_layout_comments_quotes_unicode():
    grid = loads(MIXED)
    assert (grid.xmin, grid.xmax) == (3.25, 5.25)
    assert grid.tiers[0].intervals[0].label == 'ʔa! "hi"'
    assert grid.tiers[0].intervals[1].label == "second\nline"
    assert grid.tiers[1].points[0].label == "\\ct"


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "utf-16-be"])
def test_roundtrip_text_formats_and_encodings(short, encoding):
    grid = loads(MIXED)
    text = dumps(grid, short=short)
    data = text.encode(encoding)
    if encoding == "utf-16-be":
        data = b"\xfe\xff" + data
    assert semantic(loads(data)) == semantic(grid)


@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r"])
def test_line_endings_preserve_literal_labels(separator):
    data = MIXED.replace("\n", separator)
    grid = loads(data)
    assert grid.tiers[0].intervals[1].label == f"second{separator}line"
    assert semantic(loads(dumps(grid))) == semantic(grid)


def test_short_header_and_empty_point_tier():
    grid = loads('"ooTextFile short"\n"TextGrid"\n0 1 <exists> 1 "TextTier" "events" 0 1 0')
    assert grid.tiers[0].points == ()


def test_weak_domain_mismatch_survives_roundtrip():
    grid = TextGrid(
        "mismatch",
        0,
        10,
        (
            IntervalTier("phones", 1, 9, (Interval(2, 3, "a"), Interval(3, 8, "b"))),
            PointTier("events", 0, 10, (Point(11, "outside"),)),
        ),
    )
    result = loads(dumps(grid))
    assert semantic(result) == semantic(grid)
    assert len(result.domain_warnings()) == 3


@pytest.mark.parametrize(
    "data",
    [
        b"ooBinaryFileTextGrid",
        b"\xffbroken",
        '"ooTextFile" "Sound" 0 1',
        '"ooTextFile" "TextGrid" 0 1 <exists> 1 "OtherTier" "x" 0 1 0',
        '"ooTextFile" "TextGrid" 0 1 <exists> 2',
        '"ooTextFile" "TextGrid" 0 1 <exists> -1',
        '"ooTextFile" "TextGrid" 0 1 <exists> 1.5',
        '"ooTextFile" "TextGrid" 0 1 <exists> 0 999',
        '"ooTextFile" "TextGrid" 0 1 <exists> 1 "IntervalTier" "x" 0 1 1 0 1 "unclosed',
        '"ooTextFile" "TextGrid" 0 1e999 <exists> 0',
        '"ooTextFile" "TextGrid" NaN 1 <exists> 0',
    ],
)
def test_invalid_or_unsupported_input(data):
    with pytest.raises(InvalidInput):
        loads(data)


def test_geometry_validation_and_resource_limits():
    with pytest.raises(InvalidInput, match="adjacent"):
        IntervalTier("bad", 0, 1, (Interval(0, 0.4), Interval(0.5, 1)))
    with pytest.raises(InvalidInput, match="strictly"):
        PointTier("bad", 0, 1, (Point(0.5), Point(0.5)))
    with pytest.raises(InvalidInput):
        Interval(1, 1)
    for limits in (
        Limits(max_bytes=10),
        Limits(max_tiers=1),
        Limits(max_entities=1),
        Limits(max_string=3),
    ):
        with pytest.raises(InvalidInput):
            loads(MIXED, limits=limits)


def test_doubles_empty_labels_no_normalization():
    grid = TextGrid(
        "precision",
        -0.5,
        1.1234567890123457,
        (
            IntervalTier(
                "phones",
                -0.5,
                1.1234567890123457,
                (
                    Interval(-0.5, 0.12345678901234568, ""),
                    Interval(0.12345678901234568, 1.1234567890123457, " e\u0301  "),
                ),
            ),
        ),
    )
    assert semantic(loads(dumps(grid))) == semantic(grid)


def test_atomic_no_clobber_and_overwrite(tmp_path, monkeypatch):
    import langtools_praat.io.atomic as atomic

    target = tmp_path / "phones.TextGrid"
    original = loads(MIXED)
    write(target, original)
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        write(target, TextGrid.create("other", 0, 1, (("words", "interval"),)))
    assert target.read_bytes() == before

    def fail_replace(*args):
        raise PermissionError("simulated disk failure")

    monkeypatch.setattr(atomic.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        write(target, original, overwrite=True)
    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]
    assert semantic(read(target)) == semantic(original)
