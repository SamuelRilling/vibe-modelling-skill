"""Deterministic checks and EXPECT values for vibe-modelling build specs. Standard library only; all values in mm.

Commands (run with -h for details):
  boltcircle  hole spacing and coordinates on a bolt circle
  edge        hole-center-to-edge distance against the process minimum
  wall        wall left between two diameters against the process minimum
  plate       bbox and volume of a plate with rounded corners and (stepped) holes
  revolve     bbox and volume of a turned part from its half-profile polygon

Exit code 1 means a check failed; the output says which.
"""
import argparse
import math
import sys
from collections.abc import Iterable

MIN_WALL = {"machined": 1.0, "fdm": 1.2, "molded": 1.0}
MIN_EDGE_RATIO = {"machined": 1.0, "fdm": 1.0, "molded": 1.0}  # center-to-edge / hole Ø
BOLTED_EDGE_RATIO = 1.5


Point = tuple[float, float]
Bbox = tuple[float, float, float]


def bolt_circle(bcd: float, n: int, hole_d: float, start_deg: float = 0.0) -> tuple[float, list[Point]]:
    """Return (gap between neighbouring holes, list of (x, y) centers)."""
    gap = bcd * math.sin(math.pi / n) - hole_d
    centers = [
        (bcd / 2 * math.cos(math.radians(start_deg + 360 * i / n)), bcd / 2 * math.sin(math.radians(start_deg + 360 * i / n)))
        for i in range(n)
    ]
    return gap, centers


def edge_ok(
    hole_d: float, center_dist: float, process: str, bolted: bool = False, thickness: float | None = None
) -> tuple[bool, str]:
    """Return (ok, message) for a hole near an edge."""
    if process == "sheet":
        if thickness is None:
            raise ValueError("sheet metal needs --thickness")
        clear = center_dist - hole_d / 2
        ok = clear >= 2 * thickness and hole_d >= thickness
        return ok, "hole edge to part edge %.2f (min %.2f), hole Ø %.2f (min %.2f)" % (clear, 2 * thickness, hole_d, thickness)
    ratio = center_dist / hole_d
    minimum = BOLTED_EDGE_RATIO if bolted else MIN_EDGE_RATIO[process]
    return ratio >= minimum, "center to edge = %.2f × Ø (min %.2f × Ø)" % (ratio, minimum)


def wall(outer_d: float, inner_d: float) -> float:
    return (outer_d - inner_d) / 2


def parse_hole(spec: str) -> tuple[int, list[tuple[float, float | None]]]:
    """'[Nx]D[:depth][,D:depth...]' -> (count, [(d, depth or None)]). Depths from the top face; no depth = through."""
    count = 1
    if "x" in spec:
        count_text, spec = spec.split("x", 1)
        count = int(count_text)
    steps = []
    for part in spec.split(","):
        d, _, depth = part.partition(":")
        steps.append((float(d), float(depth) if depth else None))
    return count, steps


def hole_volume(steps: list[tuple[float, float | None]], thickness: float) -> float:
    """Volume removed by one stepped hole: the largest diameter present at each depth band."""
    depths = sorted({thickness} | {min(depth, thickness) for _, depth in steps if depth is not None})
    removed, top = 0.0, 0.0
    for bottom in depths:
        widest = max(d for d, depth in steps if depth is None or depth >= bottom)
        removed += math.pi * widest ** 2 / 4 * (bottom - top)
        top = bottom
    return removed


def plate(
    length: float, width: float, thickness: float, corner_r: float = 0.0, holes: Iterable[str] = ()
) -> tuple[Bbox, float]:
    """Return (bbox, volume). holes: iterable of parse_hole specs."""
    volume = length * width * thickness - 4 * (corner_r ** 2 - math.pi * corner_r ** 2 / 4) * thickness
    for spec in holes:
        count, steps = parse_hole(spec)
        volume -= count * hole_volume(steps, thickness)
    return (length, width, thickness), volume


def parse_profile(text: str) -> list[Point]:
    """'r,y r,y ...' -> [(r, y)]."""
    points = []
    for point in text.split():
        r, y = point.split(",")
        points.append((float(r), float(y)))
    return points


def revolve(points: list[Point]) -> tuple[Bbox, float]:
    """Return (bbox, volume) of a half-profile polygon (r >= 0) revolved about the vertical axis."""
    if any(r < 0 for r, _ in points):
        raise ValueError("profile radii must be >= 0")
    volume = 0.0
    for (r1, y1), (r2, y2) in zip(points, points[1:] + points[:1]):
        volume += math.pi * (y2 - y1) * (r1 * r1 + r1 * r2 + r2 * r2) / 3
    diameter = 2 * max(r for r, _ in points)
    height = max(y for _, y in points) - min(y for _, y in points)
    return (diameter, height, diameter), abs(volume)


def print_bbox_volume(bbox: Bbox, volume: float) -> None:
    print("bbox: %g × %g × %g (width × height × depth, height along up)" % bbox)
    print("volume: %.1f mm³" % volume)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("boltcircle", help="hole spacing and coordinates on a bolt circle")
    p.add_argument("--bcd", type=float, required=True, help="bolt circle diameter")
    p.add_argument("--n", type=int, required=True, help="number of holes")
    p.add_argument("--hole", type=float, required=True, help="hole diameter")
    p.add_argument("--start", type=float, default=0.0, help="angle of the first hole, degrees from +x")

    p = sub.add_parser("edge", help="hole-center-to-edge distance against the process minimum")
    p.add_argument("--hole", type=float, required=True, help="hole diameter")
    p.add_argument("--center", type=float, required=True, help="distance from hole center to the part edge")
    p.add_argument("--process", choices=sorted(MIN_EDGE_RATIO) + ["sheet"], required=True)
    p.add_argument("--bolted", action="store_true", help="hole carries a bolt load (min 1.5 × Ø)")
    p.add_argument("--thickness", type=float, help="sheet thickness (sheet metal only)")

    p = sub.add_parser("wall", help="wall left between two diameters against the process minimum")
    p.add_argument("--outer", type=float, required=True, help="outer diameter")
    p.add_argument("--inner", type=float, required=True, help="inner diameter")
    p.add_argument("--process", choices=sorted(MIN_WALL), required=True)

    p = sub.add_parser("plate", help="bbox and volume of a plate")
    p.add_argument("--l", type=float, required=True, help="length")
    p.add_argument("--w", type=float, required=True, help="width")
    p.add_argument("--t", type=float, required=True, help="thickness")
    p.add_argument("--corner-r", type=float, default=0.0, help="vertical corner radius")
    p.add_argument("--hole", action="append", default=[], help="'[Nx]D[:depth][,D:depth...]', repeatable; e.g. 4x5.5 or 16,22:4")

    p = sub.add_parser("revolve", help="bbox and volume of a turned part")
    p.add_argument("--profile", required=True, help="half-profile as 'r,y r,y ...' (r = radius from axis, y = height)")

    args = parser.parse_args(argv)
    try:
        return run(args)
    except ValueError as error:
        print("error: %s" % error, file=sys.stderr)
        return 2


def run(args: argparse.Namespace) -> int:
    if args.command == "boltcircle":
        gap, centers = bolt_circle(args.bcd, args.n, args.hole, args.start)
        print("gap between holes: %.2f" % gap)
        print("outer extent radius: %.2f" % (args.bcd / 2 + args.hole / 2))
        print("centers: " + "  ".join("(%.2f, %.2f)" % c for c in centers))
        if gap <= 0:
            print("FAIL: holes overlap")
            return 1
    elif args.command == "edge":
        ok, message = edge_ok(args.hole, args.center, args.process, args.bolted, args.thickness)
        print(("OK: " if ok else "FAIL: ") + message)
        return 0 if ok else 1
    elif args.command == "wall":
        thickness, minimum = wall(args.outer, args.inner), MIN_WALL[args.process]
        ok = thickness >= minimum
        print("%s: wall %.2f (min %.2f for %s)" % ("OK" if ok else "FAIL", thickness, minimum, args.process))
        return 0 if ok else 1
    elif args.command == "plate":
        print_bbox_volume(*plate(args.l, args.w, args.t, args.corner_r, args.hole))
    elif args.command == "revolve":
        print_bbox_volume(*revolve(parse_profile(args.profile)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
