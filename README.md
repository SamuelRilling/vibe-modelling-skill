# vibe-modelling-skill

A Claude skill that turns "make me a bracket for a motor" into a complete, buildable CAD spec before anything is modeled. It proposes concrete values for what's missing, reports its assumptions, and asks "Send now or change anything?".

## What it does

CAD programs build exactly what they are given. Natural-language requests leave most of a part undefined: "small hole", "thin plate", no origin, no material. The skill sits between the user and the CAD program and fixes that first.

- **Proposes instead of asking.** Every gap gets a value with a reason: "Holes → Ø4.5 mm (clearance for M4). OK?"
- **Three modes.** `draft` needs only the shape and size; `normal` adds function, feature sizes and material; `strict` requires everything, down to positions and tolerances.
- **Checks the design.** Holes outside the part, pockets deeper than the plate, overlapping bolt circles, walls too thin for the process.
- **Reports assumptions** in plain sentences: "You didn't specify the plate thickness, so I went with 3 mm."
- **Hands off a build spec**: a numbered feature list with parameters and an EXPECT block the CAD agent can check its result against.
- **Same conventions every time**: up is the top-plane normal, the origin sits on the mating interface, and changes after a build go out as a delta.

## Example

> **You:** a plate to mount a NEMA 17 motor, aluminum
>
> **Skill:** proposes a 60 × 60 × 5 mm plate, the NEMA 17 bolt pattern (31 mm, M3 clearance Ø3.4), a Ø22.5 pilot bore, the origin on the bore axis at the mounting face, then lists its assumptions and ends with "Send now or change anything?"

## Install

Copy `skills/vibe-modelling-skill/` into your Claude skills folder (for Claude Code: `~/.claude/skills/`). It triggers when you describe a part to model.

It works on its own (it outputs the build spec). With a CAD tool connected, such as a SolidWorks MCP server, the spec is handed over for building.

## How it decides

- **A part is fully defined** when its interfaces, envelope, datum and process are known, and every feature has four slots filled: what, size, where, how far.
- **Least information wins**: a standard name ("M5", "608") beats a relation ("centered", "8 mm from the edge"), which beats a raw number.
- **Questions are aimed by leverage**: interfaces first (one answer fixes many dimensions), finishing details last.
- **The handoff is a structured feature list**, not prose or code. Prose is ambiguous; code ties the spec to one CAD program.

## Docs

- [SKILL.md](skills/vibe-modelling-skill/SKILL.md): the skill itself.
- [docs/conventions.md](docs/conventions.md): the orientation, origin and iteration rules, and why.
- [docs/prompt-research.md](docs/prompt-research.md): research on what makes a good CAD prompt and handoff format.
- [docs/test-run-1.md](docs/test-run-1.md): gate tests on 5 prompts and two parts built in SolidWorks.

## Status

v0.3, early. Tested on prismatic and turned parts in SolidWorks 2020. Assemblies, drawings and freeform shapes are out of scope.
