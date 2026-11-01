"""Check a vibe-modelling build spec or delta spec against the format in docs/build-spec.md. Standard library only.

Usage: python lint_spec.py SPEC_FILE   (or "-" to read stdin)
Prints ERROR / WARN lines; exit code 1 if any ERROR.
"""
import re
import sys
from dataclasses import dataclass

FULL_HEADERS = ("PART", "ORIENTATION", "DATUM", "PARAMETERS", "EXPECT")
DELTA_HEADERS = ("DELTA", "CHANGED", "AFFECTED", "EXPECT")
NEEDS_END_CONDITION = re.compile(r"\b(extrude|cut|hole|revolve|boss)\b", re.I)
END_CONDITION = re.compile(r"\b(blind|through|up to|mid-plane|offset)\b|\d+\s*°", re.I)
FORBIDDEN_REFERENCES = (
    (re.compile(r"\b(Face|Edge|Plane|Sketch|Vertex)\d+\b"), "index-based reference"),
    (re.compile(r"\b(Cut|Boss)-Extrude\d+\b|\b(Fillet|Chamfer|Revolve)\d+\b"), "CAD-generated feature name"),
    (re.compile(r"\b(Planta|Alzado|Vista lateral|Plano \w+)\b"), "localized plane name; use top / front / right"),
)
FEATURE = re.compile(r"^(\d+)\.\s+([^:·]+):\s*(.*)$")
PARAMETER = re.compile(r"([A-Za-z_]\w*)=(\S+)")
NAME = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class Feature:
    line: int
    number: int
    name: str
    body: str


def parse(text: str) -> tuple[dict[str, tuple[int, str]], list[Feature]]:
    """Return headers {KEY: (line, value)} and features; indented lines continue the previous feature."""
    headers: dict[str, tuple[int, str]] = {}
    features: list[Feature] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        feature = FEATURE.match(line)
        header = re.match(r"^([A-Z]+):\s*(.*)$", line)
        if feature:
            features.append(Feature(number, int(feature.group(1)), feature.group(2).strip(), feature.group(3)))
        elif header and not raw[0].isspace():
            headers[header.group(1)] = (number, header.group(2))
        elif features and raw[0].isspace():
            last = features.pop()
            features.append(Feature(last.line, last.number, last.name, last.body + " " + line))
    return headers, features


def lint(text: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    headers, features = parse(text)
    is_delta = "DELTA" in headers
    errors = ["missing %s line" % key for key in (DELTA_HEADERS if is_delta else FULL_HEADERS) if key not in headers]
    for number, raw in enumerate(text.splitlines(), start=1):
        for pattern, reason in FORBIDDEN_REFERENCES:
            match = pattern.search(raw)
            if match:
                errors.append("line %d: %s (%s)" % (number, reason, match.group(0)))
    if is_delta:
        return errors, []

    if "PART" in headers:
        line, value = headers["PART"]
        if not re.match(r"^\S+ v\d+\b", value):
            errors.append("line %d: PART has no version after the part name (motor-plate v1)" % line)
        if "units" not in value:
            errors.append("line %d: PART has no units" % line)
    errors += check_features(features)
    parameter_errors, warnings = check_parameters(headers, text)
    return errors + parameter_errors, warnings


def check_features(features: list[Feature]) -> list[str]:
    if not features:
        return ["no numbered features"]
    errors = []
    expected = list(range(1, len(features) + 1))
    if [f.number for f in features] != expected:
        errors.append("features are not numbered 1..%d in order" % len(features))
    names = [f.name.lower() for f in features]
    errors += ["line %d: feature name %r used twice" % (f.line, f.name) for f in features if names.count(f.name.lower()) > 1]
    for f in features:
        slots = [s for s in f.body.split("·") if s.strip()]
        if len(slots) < 2:
            errors.append("line %d: %s has fewer than 2 slots; separate what · where · how far with ' · '" % (f.line, f.name))
        if NEEDS_END_CONDITION.search(slots[0] if slots else "") and not END_CONDITION.search(f.body):
            errors.append("line %d: %s has no end condition (blind, through all, up to, mid-plane, angle)" % (f.line, f.name))
    return errors


def check_parameters(headers: dict[str, tuple[int, str]], text: str) -> tuple[list[str], list[str]]:
    if "PARAMETERS" not in headers:
        return [], []
    line, value = headers["PARAMETERS"]
    parameters = dict(PARAMETER.findall(value))
    errors = [
        "line %d: %s uses undefined %s" % (line, name, used)
        for name, expression in parameters.items()
        for used in NAME.findall(expression)
        if used not in parameters
    ]
    without_definitions = PARAMETER.sub(lambda m: m.group(2), text)
    warnings = [
        "parameter %s is defined but never used" % name
        for name in parameters
        if not re.search(r"(?<![\w.])%s(?!\w)" % re.escape(name), without_definitions)
    ]
    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    text = sys.stdin.read() if argv[0] == "-" else open(argv[0], encoding="utf-8").read()
    errors, warnings = lint(text)
    for message in errors:
        print("ERROR " + message)
    for message in warnings:
        print("WARN " + message)
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
