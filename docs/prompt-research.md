# What makes a good CAD modelling prompt — research notes

Date: 2026-11-01. Feeds `skills/vibe-modelling-skill/SKILL.md`.

## 1. Evidence

| Source | Finding |
|---|---|
| Text2CAD (Khan et al., 2024, arXiv 2409.17106) | Four prompt levels, from abstract ("two concentric cylinders") to expert ("draw a rectangle from (x1,y1) to (x2,y2), extrude along z"). The detailed level beat the baseline by ~27 points (63% vs 36%); abstract prompts showed almost no gap. Detail that mirrors the construction sequence is what helps. |
| CADIR (2026, arXiv 2608.00891) | An editable IR (operations + parameters + dependencies + constraints + topology selection) beat raw CadQuery/build123d scripts and reached 100% execution success. Main failure causes: index-based face/edge selection, implicit workplanes, unclear errors. SolidWorks had the lowest edit success (92%). |
| CADCodeVerify (ICLR 2025, arXiv 2410.05340) | Generating verification questions, then checking a render against them, cut geometric error ~7%. Verification is worth writing into the spec. |
| SolidPilot / mcp-server-solidworks | LLM emits a CAD-neutral feature graph; a deterministic compiler emits SolidWorks COM calls. Same idea as CADIR, unbenchmarked. |
| Zoo docs | Missing dimensions get filled by "industry standard" guesses; simple mechanical parts work best; results vary between runs. |
| PrintPal guide | Envelope before features; each feature = size + position from a named edge/center + depth; name hardware ("M3 clearance hole"); state fits in mm per side; say what touches what; one change per follow-up. Top failures: mixed units, positions with no reference, nominal hole sizes for fasteners, vague qualities, unstated relationships, batched edits. |
| Leo AI guide | Lead with constraints (envelope, loads, fasteners, mating surfaces) before shape; state process early; standards as shorthand (NEMA 23, ASME B16.5, 6205-2RS); edit by naming the feature. |
| Parametric practice (Onshape, Altair, PTC forums) | Fully defined sketches: every entity's size and position pinned by a dimension or relation. Under-defined geometry moves unpredictably on edit. Dimensions should carry design intent. |

Caveat: the guides are vendor blogs; the papers are about code-CAD generation, not SolidWorks-MCP chat. The direction agrees across all of them.

## 2. The minimal complete definition

A prismatic part is a **base body plus an ordered list of features**. It is fully described when:

**Part level (4 items)**
1. **Interfaces:** what it mates with, bolts to, holds or slides on. This is the highest-leverage information, because one standard name fixes many dimensions (an M5 bolt sets the hole, counterbore, edge distance; a 608 bearing sets bore, OD, fit, depth).
2. **Envelope:** overall size.
3. **Datum:** origin and the symmetry planes.
4. **Process:** sets wall, radius, draft and fit rules.

**Feature level (4 slots each)**
1. **What:** the operation (boss, cut, hole, fillet, pattern…).
2. **Size:** its own dimensions.
3. **Where:** sketch plane or face, plus position relative to a datum or another feature.
4. **How far:** end condition (blind depth, through all, up to face) and direction.

A feature with any empty slot is under-defined. That is the completeness test the skill applies.

**Least information:** relations replace numbers. "Centered", "symmetric", "concentric with the bore", "4× on a 40 mm bolt circle", "8 mm in from each edge" each remove several degrees of freedom with one phrase. Standards do the same for interface geometry. Prefer, in order: standard name → relation → explicit number.

## 3. Where questions should aim

Order by **leverage × cost of being wrong**:

1. Interfaces and function (one answer → many dimensions; wrong = part doesn't fit).
2. Envelope and process.
3. Feature sizes and positions that touch an interface.
4. Free features (positions not tied to anything).
5. Finishing (fillets, chamfers, text): default, don't ask.

Never ask for what a relation or standard already implies. Ask about the one thing that unlocks the rest.

## 4. What the input to the CAD side should look like

| Form | Verdict |
|---|---|
| Natural language prose | Good between user and agent. Bad as the final handoff: no slot structure, ambiguous references. |
| Pure math / coordinates only | Precise but loses design intent; edits break the relations. Use coordinates only where computed (bolt-circle positions). |
| Raw API code | Tied to one MCP; the executor should write it, not the spec. |
| **Structured feature list (chosen)** | Ordered features, each with the four slots, named driving parameters, references by datum and feature name, plus expected results to verify. Matches Text2CAD's best level and CADIR's IR shape while staying MCP-agnostic. A later MCP integration can parse it directly. |

Rules for the handoff:
- Absolute values with units; computed positions written out (don't make the executor do trig).
- Name every feature; refer to faces and edges by feature + description ("top face of Base", "4 vertical edges of Base"), never by index.
- Named parameters for the driving dimensions, so a later change is a single value.
- End with expected results (bounding box, feature count, hole count, key dimensions) so the executor can check its work.

## Sources
- https://arxiv.org/html/2409.17106v1
- https://arxiv.org/html/2608.00891v1
- https://arxiv.org/abs/2410.05340v1
- https://github.com/eyfel/mcp-server-solidworks
- https://docs.zoo.dev/docs/zoo-design-studio/text-to-cad
- https://printpal.io/wiki/text-to-cad-prompting-guide
- https://www.getleo.ai/blog/text-to-cad-prompt-engineering-guide
- https://forum.onshape.com/discussion/25425/what-does-fully-defined-mean
- https://help.altair.com/polyfoam/en_us/topics/shared/parametric/sketching/sketch_issues_r.htm
