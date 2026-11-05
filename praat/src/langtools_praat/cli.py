"""Headless entry point; importing it never imports Qt or opens an audio device."""

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from . import __version__
from .annotation.session import AnnotationSession
from .application.workspace import Workspace
from .errors import InvalidInput
from .io.atomic import save_bytes
from .io.audio import AudioFile
from .io.textgrid import read, write
from .model.textgrid import IntervalTier, TextGrid


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="LangTools Praat audio and annotation prototype")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Print audio or TextGrid metadata as JSON")
    inspect.add_argument("input", type=Path)
    create = commands.add_parser("new-textgrid", help="Create tiers covering a WAV time domain")
    create.add_argument("input", type=Path)
    create.add_argument("output", type=Path)
    create.add_argument("--interval-tier", action="append", default=[])
    create.add_argument("--point-tier", action="append", default=[])
    convert = commands.add_parser("convert-textgrid", help="Convert full/short TextGrid text")
    convert.add_argument("input", type=Path)
    convert.add_argument("output", type=Path)
    convert.add_argument("--short", action="store_true")
    label = commands.add_parser("set-label", help="Edit a label through the shared command layer")
    label.add_argument("input", type=Path)
    label.add_argument("output", type=Path)
    label.add_argument("--tier", type=int, required=True, help="One-based tier position")
    label.add_argument("--item", type=int, required=True, help="One-based interval/point position")
    label.add_argument("--label", required=True)
    export = commands.add_parser("export-annotations", help="Export annotations as UTF-8 CSV")
    export.add_argument("input", type=Path)
    export.add_argument("output", type=Path)
    for command in (create, convert, label, export):
        command.add_argument("--overwrite", action="store_true")
    gui = commands.add_parser("gui", help="Launch the optional Qt desktop editor")
    gui.add_argument("files", type=Path, nargs="*")
    return root


def metadata(path: Path) -> dict:
    if path.suffix.lower() != ".textgrid":
        return AudioFile.open(path).describe()
    grid = read(path)
    return {
        "kind": "TextGrid",
        "name": grid.name,
        "xmin": grid.xmin,
        "xmax": grid.xmax,
        "warnings": grid.domain_warnings(),
        "tiers": [
            {
                "name": t.name,
                "kind": "IntervalTier" if isinstance(t, IntervalTier) else "TextTier",
                "xmin": t.xmin,
                "xmax": t.xmax,
                "count": len(t.intervals if isinstance(t, IntervalTier) else t.points),
            }
            for t in grid.tiers
        ],
    }


def run(args: argparse.Namespace) -> int:
    if args.command == "gui":
        try:
            from .gui.app import launch
        except ModuleNotFoundError as error:
            if error.name in ("PySide6", "pyqtgraph"):
                raise InvalidInput(
                    "Install the desktop extra: uv sync --locked --extra gui"
                ) from error
            raise
        return launch(args.files)
    if args.command == "inspect":
        print(json.dumps(metadata(args.input), ensure_ascii=False, indent=2, allow_nan=False))
    elif args.command == "new-textgrid":
        source = AudioFile.open(args.input)
        tiers = [(name, "interval") for name in args.interval_tier]
        tiers += [(name, "point") for name in args.point_tier]
        if not tiers:
            tiers = [("words", "interval")]
        grid = TextGrid.create(args.output.stem, source.axis.xmin, source.axis.xmax, tuple(tiers))
        write(args.output, grid, overwrite=args.overwrite)
    elif args.command == "convert-textgrid":
        write(args.output, read(args.input), short=args.short, overwrite=args.overwrite)
    elif args.command == "set-label":
        workspace = Workspace()
        object_id = workspace.open(args.input)
        target = workspace.get(object_id)
        if not isinstance(target, AnnotationSession):
            raise InvalidInput("Label editing requires a TextGrid.")
        if not 1 <= args.tier <= len(target.document.tiers):
            raise InvalidInput("Tier position is outside the TextGrid.")
        tier = target.document.tiers[args.tier - 1]
        entities = tier.intervals if isinstance(tier, IntervalTier) else tier.points
        if not 1 <= args.item <= len(entities):
            raise InvalidInput("Item position is outside the tier.")
        workspace.execute(
            object_id,
            "annotation.set_label",
            expected_revision=target.document.revision,
            tier_id=tier.id,
            entity_id=entities[args.item - 1].id,
            label=args.label,
        )
        workspace.save(object_id, args.output, overwrite=args.overwrite)
    elif args.command == "export-annotations":
        grid = read(args.input)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("tier", "type", "start_s", "end_s", "label"))
        for tier in grid.tiers:
            if isinstance(tier, IntervalTier):
                for item in tier.intervals:
                    writer.writerow(
                        (tier.name, "interval", repr(item.xmin), repr(item.xmax), item.label)
                    )
            else:
                for point in tier.points:
                    writer.writerow(
                        (tier.name, "point", repr(point.time), repr(point.time), point.label)
                    )
        save_bytes(args.output, output.getvalue().encode("utf-8"), overwrite=args.overwrite)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return run(args)
    except (InvalidInput, FileNotFoundError) as error:
        print(f"Invalid input: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Operation failed: {error}", file=sys.stderr)
        return 1
