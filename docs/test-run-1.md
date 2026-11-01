# Test run 1 — SKILL.md v0.1

Date: 2026-11-01. Method: 5 fresh Sonnet agents, each given only `SKILL.md` and one user prompt; each produced the turn-1 reply and the build spec after "send". No CAD build: `sw_mcp` returned "Not connected to SolidWorks".

| # | Prompt (type) | Result | Notes |
|---|---|---|---|
| 1 | "make me a small bracket to hold a motor" (vague) | Pass | Proposed NEMA 17 with full dims, 3 alternatives (NEMA 23, printed), tip. Hole math correct. Build spec mixes sketch-plane and model axes. |
| 2 | "draft mode: a box with a lid for an arduino uno, 3d printed" (vague, draft) | Pass, with a real fit risk | Short draft reply, 3 assumptions. Uno hole pattern correct. Board dims recalled from memory; USB-B jack overhangs the board edge ~6 mm and would hit the wall. Nothing flagged it as unverified. |
| 3 | Steel plate 50×30×3, M6 on Ø60 BC, Ø25 center, 40×20×5 pocket (conflicting) | Pass on detection | Caught all three conflicts (BC off the part, pocket deeper than plate, bore splits pocket). Overrode the user's envelope to 70×70×10 and said no alternatives exist. |
| 4 | Brass flanged bushing, fully dimensioned (complete) | Pass | Clean table, correct wall check, sensible chamfer reading. Built as stacked extrudes; a revolve is the natural method. |
| 5 | Strict 6061 motor plate with 608 seat (meant complete) | Pass | The prompt had an unintended conflict (7 mm seat in a 6 mm plate). Caught it, proposed a 4 mm seat + 2 mm shoulder, offered a 10 mm plate. Edge-distance warning correct (1.45 × Ø). |

**Criteria met in all 5:** ended with "Send now or change anything?"; no bare questions; assumptions stated in plain sentences; build spec used the four slots, named parameters and EXPECT; counts in EXPECT correct.

## Fixes for v0.2
1. When a fix changes a user-given value: smallest change that works, and always ≥ 2 options (test 3).
2. Build spec: give sketch coordinates in the sketch plane's own axes and state the mapping to model axes (test 1).
3. Turned parts: build as one revolve of the half-profile about the axis (test 4).
4. Off-the-shelf components recalled from memory: status "Resolved (from memory, check datasheet)", and include connector overhangs / keep-outs (test 2).
5. Add a feature-vs-feature interference check (bore breaking pocket walls, holes cutting into pockets) (test 3).

## Build in SolidWorks (2026-11-01)

Specs from tests 4 and 5 built in SolidWorks 2020 through `sw_mcp`, verified with a COM script (bbox, volume, features, cylinder radii).

| Part | EXPECT | Measured | Hand-calc volume | Measured volume |
|---|---|---|---|---|
| Bushing (test 4) | bbox 24 × 20 × 24 · bore Ø8 · 4 features | 24 × 20 × 24 · R4 / R6 / R12 · 4 features | ≈ 2590 mm³ | 2590.6 mm³ |
| Motor plate (test 5) | bbox 100 × 60 × 6 · 4 × Ø5.5 + Ø16 through · Ø22 seat · 5 features | 100 × 60 × 6 · R2.75 ×4, R8, R11, R3 ×4 · 5 features | 33 460.8 mm³ | 33 460.8 mm³ |

Both specs were buildable as written; no value had to be guessed. Deviations: bushing built as extrudes (spec predates the revolve fix); plate bore cut before the seat (same geometry).

**Executor friction (all `sw_mcp`, not the spec):**
- `CreateSketch` only accepts localized plane names ("Planta", not "Top").
- Cut extrudes from a plane need `reverseDirection: true`.
- `ExecuteSolidWorksApi` fails on late-bound interfaces (`IPartDoc`, `ISelectionMgr`) and on `ref`/`out` parameters; parameter names must match the interop exactly.
- No tool returns bbox / volume, so EXPECT needs an external script.
- Coordinate edge selection (`SelectByID2`) is unreliable for hidden edges; corner edges had to be selected by geometry from a script.
- `GetModelInfo` truncates the feature list.
