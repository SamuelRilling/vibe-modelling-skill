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

## Install

### As a skill (any agent)

Copy the folder `skills/vibe-modelling-skill/` from this repo into your agent's skills folder:

| Agent | Where it goes |
|---|---|
| Claude Code | `~/.claude/skills/` (all your projects) or `<project>/.claude/skills/` (one project) |
| Claude app (claude.ai, desktop) | zip the folder and upload it in Settings, under Skills |
| Codex, Gemini CLI, Copilot and other [Agent Skills](https://agentskills.io) agents | their skills folder, or a project's `.agents/skills/` |

To update, copy the folder again.

### As a plugin (Claude Code)

```
/plugin marketplace add SamuelRilling/vibe-modelling-skill
/plugin install vibe-modelling-skill@vibe-modelling
```

A **plugin** is Claude Code's package format. This one contains the same skill folder, so the skill works exactly the same; the plugin only changes how it's installed and kept up to date. Claude Code shows it as a plugin, and the skill's name gets a prefix (`vibe-modelling-skill:vibe-modelling-skill`).

| | Skill folder | Plugin |
|---|---|---|
| Works in | any Agent Skills agent | Claude Code |
| Install | copy a folder | two commands |
| Update | copy again | `claude plugin marketplace update vibe-modelling`, then `claude plugin update vibe-modelling-skill@vibe-modelling` |
| Turn off | delete the folder | `claude plugin disable` or `claude plugin uninstall` |

Use the plugin in Claude Code, the folder everywhere else. Don't do both, or the skill loads twice.

### With or without a CAD connection

**The skill doesn't build anything itself**. It turns your request into a **build spec**, a plain-text feature list, and whatever is connected to your agent does the building.

- **Skill only, no CAD connection:** you get the spec in the chat after you send. Build it by hand from the list, or paste it into an agent that is connected to CAD.
- **With a CAD MCP server** (a connector that lets the agent drive a CAD program): after you send, the agent builds the spec using that server's tools, then compares the result with the spec's EXPECT line (size, hole count, volume) if the server can measure it.
- **Another CAD program, another MCP server:** the skill works the same, because the spec names planes by role (top / front / right) and never uses one program's API or axis letters. The agent translates the spec into whichever server's tools it has. What changes is how much that server can do: if it's missing an operation (a revolve, a chamfer), the agent should say so instead of improvising.

The skill doesn't include an MCP server; install one for your CAD program separately. Tested with [sw_mcp](https://github.com/tylerstoltz/sw_mcp) on SolidWorks 2020. Writing a server or builder? See [docs/build-spec.md](docs/build-spec.md#for-builder-authors).

## Example

> **You:** a plate to mount a NEMA 17 motor, aluminum
>
> **Skill:** proposes a 60 × 60 × 5 mm plate, the NEMA 17 bolt pattern (31 mm, M3 clearance Ø3.4), a Ø22.5 pilot bore, the origin on the bore axis at the mounting face, then lists its assumptions and ends with "Send now or change anything?"

## How it decides

- **A part is fully defined** when its interfaces, envelope, datum and process are known, and every feature has four slots filled: what, size, where, how far.
- **Least information wins**: a standard name ("M5", "608") beats a relation ("centered", "8 mm from the edge"), which beats a raw number.
- **Questions are aimed by leverage**: interfaces first (one answer fixes many dimensions), finishing details last.
- **The handoff is a structured feature list**, not prose or code. Prose is ambiguous; code ties the spec to one CAD program.
- **Math is deterministic where it can be.** `scripts/geometry.py` checks bolt circles, edge distances and walls and computes bbox and volume for EXPECT; `scripts/lint_spec.py` checks a spec against the format. Both are matched against SolidWorks measurements in the tests.

## Docs

- [SKILL.md](skills/vibe-modelling-skill/SKILL.md): the skill itself.
- [docs/build-spec.md](docs/build-spec.md): the build spec format, for anyone writing a builder.
- [examples/](examples/): complete specs and a delta spec.
- [docs/conventions.md](docs/conventions.md): the orientation, origin and iteration rules, and why.
- [docs/prompt-research.md](docs/prompt-research.md): research on what makes a good CAD prompt and handoff format.
- [docs/test-run-1.md](docs/test-run-1.md): gate tests on 5 prompts and two parts built in SolidWorks.

## Status

v0.3, early. Tested on prismatic and turned parts in SolidWorks 2020. Assemblies, drawings and freeform shapes are out of scope.

Run the tests with `python -m unittest discover -s tests`. MIT licensed.
