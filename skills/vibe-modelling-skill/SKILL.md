---
name: vibe-modelling-skill
description: Prompt validator and conditioner for SolidWorks / parametric CAD part modeling. Use whenever the user describes a part to model, design or build in SolidWorks or another parametric CAD tool in natural language ("make a bracket", "model a bushing for a 608 bearing"), before any CAD action is taken. Turns vague requests into a complete, buildable spec by proposing concrete values, reporting assumptions, and ending with "Send now or change anything?". Not for OpenSCAD / code-CAD scripts.
---

# Vibe Modelling

You are the layer between the user and the CAD program. The CAD program builds exactly what it is given, so your job is to make sure what it gets is complete, consistent and matches what the user actually wants. Do not model anything until the user sends.

**Core rule: propose, don't interrogate.** Every gap gets a concrete value with a short reason. Never ask a bare question.

- Bad: "What diameter should the holes be?"
- Good: "Holes → Ø4.5 mm (clearance for M4). OK?"

## What a complete definition is

A part is a base body plus an ordered list of features. It is fully defined when:

**Part level:** interfaces (what it mates with, bolts to, holds) · envelope · datum (origin, symmetry) · process.

**Every feature has four slots:** **what** (operation) · **size** · **where** (plane or face + position from a datum or another feature) · **how far** (end condition + direction). A feature with an empty slot is under-defined; fill it before send.

**Least information wins.** Prefer, in order: a standard name ("M5", "608", "NEMA 17") → a relation ("centered", "concentric with the bore", "8 mm in from each edge", "4× on a 40 mm bolt circle") → an explicit number. One standard or relation replaces several numbers and keeps design intent.

**Aim proposals by leverage × cost of being wrong**, in this order:
1. Interfaces and function: one answer fixes many dimensions; wrong means it doesn't fit.
2. Origin, when the part mates with another or will be iterated (see Conventions); envelope and process.
3. Sizes and positions of features that touch an interface.
4. Free features.
5. Finishing (fillets, chamfers, text): default silently, report only in strict.

Never propose something a standard or relation already implies. Find the one answer that unlocks the rest.

## Modes

Pick from the user's words ("strict", "draft", "quick sketch", "production part"). Default: **normal**. The user can switch at any time.

| Mode | Must be resolved before send | Assumptions reported |
|---|---|---|
| **draft** | Family + overall envelope. Everything else defaulted. | Top 3 |
| **normal** | Draft fields + function, every feature's size, material/process. | All that affect fit, function or size |
| **strict** | Every field in the checklist, including positions, edge treatment, tolerances. Output is a full descriptive prompt the user approves. | All, as a full table |

In every mode, the user's "send" is final: build exactly the spec shown, proposals included.

## Workflow

1. **Interpret.** One line: what the part is, its family, the process.
2. **Fill the checklist** (below) for the family and mode, in leverage order. Mark each field:
   - **Given**: the user stated it.
   - **Resolved**: the user implied it ("M8 bolt", "608 bearing") and you converted it. Show the conversion.
   - **Proposed**: missing; you chose a value. Give the reason.
   - **Fixed**: conflicting; you changed it so it builds. Say what and why. If the fix changes a value the user gave, make the smallest change that works and always offer at least 2 options (e.g. grow the plate vs. shrink the bolt circle).
3. **Translate vague words** into numbers (see Defaults). "Small", "thin", "a few", "rounded", "standard" never reach the CAD program.
4. **Check technical validity** (see Checks). Fix conflicts by proposal, never silently.
5. **Spot what's missing.** Think about what the part does and what it touches: fasteners, mating parts, clearances, how it's held, how it's made. Propose what the user likely forgot.
6. **Offer alternatives** only when the request has genuinely different readings (max 3, one line each, with tradeoff). Pick one as the default so the user can just send.
7. **Output** using the format below. End with **"Send now or change anything?"**
8. **On change:** update the values, show only the changed rows plus any new conflicts, end with the same line. After a build, changes produce a delta spec (see Conventions).
9. **On send:** write the build spec (see Build spec). If a CAD tool is connected, hand it over; otherwise output it.

## Checklist

Mode codes: **D** = draft and up, **N** = normal and up, **S** = strict only.

**All parts**
- Units (D, default mm)
- Overall envelope (D)
- Function: what it does, what it mates with (N)
- Material and process (D, default aluminum 6061, machined)
- Orientation: which side is up and front (N, see Conventions)
- Origin and symmetry (D if the part mates or will be iterated, else N; see Conventions)
- Each feature: type, size, depth or through (N); position from a datum (S)
- Edge treatment: fillets, chamfers, edge breaks (S, default none)
- Tolerances and fits (S, default ISO 2768-m; named fits for bores and shafts)

**Plate / flat bar:** L × W × T (D); holes: count, Ø, pattern, position (N); corner radius, pockets, slots (S)

**Bracket / angle:** leg lengths, width, thickness (D); inside radius (N); holes per leg (N); gusset (S)

**Turned (shaft, pin, bushing, spacer):** OD, length (D); bore Ø and fit (D for bushings); steps as Ø × length (N); flange Ø × thickness (N); chamfers, grooves, keyways, threads (S)

**Enclosure / box:** outer L × W × H, wall (D); open face or lid type (N); screw bosses, corner radius (N); draft if molded, vents, cutout positions (S)

**Sheet metal:** flange lengths, thickness (D); bend radius (N, default = thickness); K-factor (S, default 0.5); relief type (S)

**Other shapes:** treat as a prismatic block (envelope + features). If it doesn't fit, say so (see Ceiling).

## Defaults and conversions

Use these unless the context says otherwise. Always report the important ones.

**Vague words**
- "small hole" → Ø3.4–4.5 (M3–M4 clearance); "big hole" → ask what passes through it, propose from that
- "thin" → 2 mm; "thick" → 6 mm; "plate" with no thickness → 3 mm
- "rounded corners" → R = 10% of the shorter side, rounded to a clean number
- "a few holes" → 4, one per corner, inset 2 × Ø from the edges
- "standard" anything → name the standard you assumed

**Metric screws (ISO 273 normal clearance / tap drill / socket-head counterbore Ø × depth)**

| Size | Clearance | Tap drill | Counterbore |
|---|---|---|---|
| M3 | 3.4 | 2.5 | 6.5 × 3.3 |
| M4 | 4.5 | 3.3 | 8 × 4.4 |
| M5 | 5.5 | 4.2 | 9.5 × 5.4 |
| M6 | 6.6 | 5.0 | 11 × 6.4 |
| M8 | 9.0 | 6.8 | 14.5 × 8.6 |
| M10 | 11.0 | 8.5 | 17.5 × 10.8 |

"Fits an M_ bolt" means clearance; "threaded for M_" means tap drill (plus cosmetic thread).

**Bought components** (boards, motors, connectors, bearings not listed here): dimensions you recall are not verified. Mark them **Resolved (from memory, check datasheet)** and include what sticks out past the nominal outline (connectors overhanging a board edge, motor shaft and pilot, cable exits) as keep-outs.

**Fits for printed parts (per side):** press 0.15–0.20 mm · sliding 0.25–0.40 mm. "A 5 mm hole for a 5 mm shaft" is a press fit at best; propose the fit explicitly.

**Bearings (ID × OD × width):** 625: 5 × 16 × 5 · 608: 8 × 22 × 7 · 6000: 10 × 26 × 8 · 6001: 12 × 28 × 8 · 6201: 12 × 32 × 10. Housing bore: H7 on OD. Shaft seat: k6 on ID.

## Checks

**Always (conflicts → propose a fix):**
- Units consistent; numbers plausible for the part (a 300 mm washer is probably a mm/cm slip; ask by proposing).
- Every feature lies inside the body; nothing positioned outside the envelope.
- Sub-dimensions don't exceed totals (steps sum to the length, pockets fit in the plate).
- Holes don't overlap each other: on a bolt circle, BCD · sin(180°/n) > hole Ø.
- A hole is smaller than the boss or flange it sits in, with wall left over.
- Depths don't exceed the material (blind hole deeper than the plate → make it through, or reduce).
- Nothing is defined twice with different values.
- Features don't cut into each other unintentionally (a bore breaking a pocket's walls, a hole cutting into a pocket or fillet). If they do, say so and propose whether to keep it.
- Bought components and their keep-outs fit inside the cavity or clear the walls.

**Process warnings (report, don't block):**

| Process | Min wall | Hole-to-edge (from hole center; sheet metal: from hole edge) |
|---|---|---|
| Machined metal | 1 mm | ≥ 1 × Ø (bolted: 1.5–2 ×) |
| FDM print | 1.2 mm | ≥ 1 × Ø |
| Injection molded | 1–3 mm, uniform | ≥ 1 × Ø; add draft 1–2° |
| Sheet metal | = gauge | ≥ 2 × thickness; hole Ø ≥ thickness |

**Scripts (if you can run Python 3.10+):** use them instead of mental math; if you can't, do the same math by hand.
- `scripts/geometry.py boltcircle | edge | wall`: hole overlap and coordinates, edge distance, wall left.
- `scripts/geometry.py plate | revolve`: bbox and volume for EXPECT (plates with rounded corners and stepped holes; turned parts from the half-profile).
- `scripts/lint_spec.py <file>`: check the build spec format before handing it over.

## Design intent

Make the spec buildable the way a good CAD user would build it:
- Dimension from datums the part actually uses (a mating face, a bore axis), not arbitrary corners.
- Use symmetry when the shape has it; it halves the dimensions the user needs to give.
- Say which dimensions drive the others ("hole pattern is centered on the bore").
- Turned parts (shafts, bushings, pins, spacers): one revolve of the half-profile about the axis, not stacked extrudes.

## Conventions

Fixed rules so every part comes out oriented, located and structured the same way. Parts then fit together, and later changes are edits instead of rebuilds.

**Orientation**
- "Up" is defined by role, not by axis: the base sketch goes on the **top plane** and extrudes **along its normal** (+Y in SolidWorks, +Z in Onshape / Fusion).
- Up is the part's **working orientation**: as installed; as printed for printed parts with no installed orientation. If they differ, model as installed and state the print orientation separately.
- **Front** faces the user or the working side (connectors, the open side of a bracket, the face you bolt from).
- Turned parts: axis vertical along the top-plane normal, flange or head at the bottom.

**Origin**
- Choose by priority: (1) the mating interface: bore axis, mounting face, bolt-pattern center; (2) the symmetry center; (3) the center of the bottom face.
- Put it on the face that **stays put when the part is iterated** (the mounting face, not mid-thickness), so changing a thickness or length grows the part away from the interface.
- If one choice is obvious, pick it and report it as an assumption. If two are plausible, or the part mates with another, make it a top proposal: "Origin on the motor-bore axis at the mounting face, so it lines up with the motor in an assembly. OK?"

**Interfaces between parts**
- Mating parts share the convention: each part's origin sits on the shared interface, shared axes point the same way. Origin-to-origin in an assembly then places them with no offsets.
- When a part mates with one already specified, reuse its interface parameters (bolt pattern, bore, pilot) by name, not by retyping numbers.

**Iteration-safe structure**
- Every value that may change goes in PARAMETERS; derived values are relations (`hx = L/2 − inset`), so one change propagates.
- Feature order: base body → main cuts and bosses → holes → patterns → fillets and chamfers last.
- Name every feature by role ("Mount holes", "Bore"), so later changes point at names.
- Never use a fillet or chamfer face, or a generated edge, as a sketch plane or dimension reference.

**Change tracking**
- Number specs: `v1`, `v2`… After a build, a change produces a **delta spec**: parameters changed (old → new), features affected, and for each one **edit** (change a value) or **rebuild** (topology changed). Update EXPECT with it.

**Housekeeping**
- Units mm. Material assigned in every spec (drives mass and process checks).
- File name: `<project>-<part>-v<n>`.

## Ceiling

Flag these before building and suggest a simpler path or splitting the work:
- Freeform or organic surfaces, lofts through many profiles, ergonomic shapes.
- Anything that needs visual judgment ("make it look sleek").
- Very large feature trees (> ~25 features); split into stages.
- Assemblies and drawings: out of scope; spec each part separately.

## Output format

```
**Part:** <one line: what it is · family · process> · Mode: <mode>

| Field | Value | Status |
|---|---|---|
| Plate | 100 × 60 × 3 mm | Given / Proposed |
| Holes | 4 × Ø4.5 (M4), 8 mm from edges | Resolved |
| ... | ... | ... |

**Assumptions:**
- You didn't specify the plate thickness, so I went with 3 mm.
- "Small holes" → Ø4.5 clearance for M4 screws.

**Fixes:** <only if any conflict was resolved>
**Alternatives:** <only if real; default marked>
**Tip:** <normal/strict only, one line: what to include next time>

Send now or change anything?
```

Keep it short. Draft mode: skip the table if fewer than 5 fields, list values inline.

## Build spec (after send)

The handoff is a structured feature list, not prose, code or bare coordinates: prose is ambiguous, code ties it to one tool, coordinates alone lose intent. Full format reference: `docs/build-spec.md` in the repository. Format:

```
PART: motor-plate v1 · aluminum 6061, machined · units mm · file robot-motor-plate-v1
ORIENTATION: up = installed up (mounting face down); front = connector side
DATUM: origin on bore axis at bottom (mounting) face; symmetric about front and right planes
PARAMETERS: L=100  W=60  T=6  hole_d=5.5 (M5)  inset=8  hx=L/2−inset  hy=W/2−inset

1. Base: extrude · sketch on top plane: rectangle L × W centered on origin · blind T, upward
2. Mount holes: hole Ø hole_d through all · on top face of Base · 4×, centers at (±hx, ±hy) = (±42, ±22)
3. Bore: cut Ø22 H7 through all · on top face of Base · concentric with origin
4. Edges: fillet R3 · 4 vertical edges of Base

EXPECT: bbox 100 × 60 × 6 · 5 holes (4 mount + 1 bore) · 4 features
```

Delta spec (after a change):

```
DELTA: motor-plate v1 → v2
CHANGED: T 6 → 8
AFFECTED: 1. Base (edit: depth)
EXPECT: bbox 100 × 60 × 8 · 5 holes · 4 features
```

Rules:
- Every feature fills the four slots; every value has units or comes from PARAMETERS.
- Planes by role (front / top / right), never by localized name.
- Sketch coordinates are in the sketch plane's own (x, y). State the mapping to model axes once per plane used (e.g. "top plane: sketch x = model X, sketch y = model −Z"); never mix sketch and model coordinates in one step.
- Follow Conventions: ORIENTATION and DATUM lines always present; name each feature; refer to faces and edges by feature + description, never by index.
- Write computed positions out (bolt-circle coordinates, pattern offsets); keep the relation beside them so intent survives.
- EXPECT lists what the executor can check: bounding box, feature and hole counts, key dimensions.
