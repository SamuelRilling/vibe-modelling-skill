# Conventions

**In short:** every part the skill specifies comes out oriented, located and structured the same way. "Up" is always the top-plane normal, the origin sits on the part's mating interface, values that may change are named parameters, and changes after a build are sent as a delta. Parts then fit together without offsets, and iterating on a design becomes a few edits instead of a rebuild.

The rules live in [SKILL.md](../skills/vibe-modelling-skill/SKILL.md#conventions). This page explains why each one is there.

## The problem

A spec can be complete and still be a poor model. Without fixed conventions, each part decides on its own which way is up, where the origin is, and how its feature tree is built. The result:

- Two parts that bolt together have unrelated origins, so placing them in an assembly needs measured offsets.
- The same part, built twice, can face different directions.
- Changing one dimension breaks features that referenced a fillet or a face created by a cut, or grows the part in the wrong direction.
- Nobody can tell what changed between two versions without rebuilding both.

None of these show up in a single test build. They show up on the second part and on the second iteration, which is where most design time goes.

## 1. Orientation

**Rule:** the base sketch goes on the top plane and extrudes along its normal. Up is the part's working orientation (as installed; as printed if there is no installed one). Front faces the user or the working side. Turned parts stand on their axis, flange or head at the bottom.

**Why by role, not by axis.** CAD programs disagree on which axis is up: SolidWorks uses +Y, Onshape and Fusion use +Z. Writing "up = +Y" would tie the spec to one program. Every one of them has a top plane, and its normal is what that program treats as up, so "sketch on top, extrude along its normal" means the same thing everywhere.

**Why working orientation.** Up has to mean something physical or it gets picked at random. The installed orientation is what assemblies, drawings and other people expect, and what views like "top" and "front" will show. For printed parts with no installed orientation, the print orientation is the meaningful one. When both exist and differ, the installed one wins, and the print orientation is stated separately, because the printer slicer can rotate the part but an assembly can't.

**Why turned parts stand up.** A revolve about the vertical axis keeps "up" consistent with every other part, and flange-down matches how such parts usually sit (a flanged bushing rests on its flange).

## 2. Origin

**Rule:** choose by priority: (1) the mating interface: bore axis, mounting face, bolt-pattern center; (2) the symmetry center; (3) the center of the bottom face. Put it on the face that stays put when the part changes. Pick it silently if obvious; make it a top proposal if two choices are plausible or the part mates with another.

**Why it matters more than it looks.** The origin is the one reference every other dimension hangs on. Everything the user later wants to change is measured from it, and every assembly mate uses it. A wrong origin doesn't make the part wrong today; it makes every later step harder. That is exactly the kind of decision worth one question.

**Why the interface first.** The interface is the part of the design that is fixed by something outside it: the motor's bolt pattern, the bearing's bore, the face that sits on the frame. Dimensions measured from it are the ones that must be right, so they should be the shortest chains. Symmetry is next because it halves the dimensions the user has to give. The bottom-face center is only a fallback.

**Why on the face that stays put.** If the origin sits in the middle of a plate's thickness, changing the thickness from 6 to 8 mm moves the mounting face by 1 mm. Every mating part is now off. With the origin on the mounting face, the plate grows away from the interface and nothing that touches it moves.

**Why it's a "preferred question".** The skill normally proposes instead of asking. The origin is the exception where a proposal should be put at the top and called out, because the cost of a wrong guess is spread over every later iteration and every mating part, and the user usually knows the answer instantly. When the choice is obvious (a single plate with one central bore), asking would be noise, so the skill picks it and reports it as an assumption.

## 3. Interfaces between parts

**Rule:** mating parts each put their origin on the shared interface, with shared axes pointing the same way. A part that mates with one already specified reuses its interface parameters by name.

**Why.** If a motor plate's origin is on the bore axis at its mounting face, and the bracket's origin is at the same point on its face, the two snap together origin-to-origin. No offsets need measuring, and if the bolt pattern changes, both parts read it from the same parameter, so they can't drift apart. This is the main gain for compatibility, and it costs nothing extra once rule 2 is followed.

## 4. Iteration-safe structure

**Rules:** every value that may change is a named parameter, and derived values are relations. Feature order is base, cuts and bosses, holes, patterns, then fillets and chamfers. Every feature is named by role. Fillet and chamfer faces, and generated edges, are never used as references.

**Why parameters and relations.** If hole positions are written as 42 and 22, widening the plate leaves the holes where they were. Written as `hx = L/2 − inset`, they follow the plate. One change propagates instead of five.

**Why this feature order.** Each feature can only reference what exists before it. Cosmetic features last means nothing structural depends on them, so they can be changed, suppressed or deleted freely. Patterns after the feature they copy keep the seed editable.

**Why names.** "Cut-Extrude3" means nothing a week later, and its number changes if the tree is rebuilt. "Bore" lets a later change say "Bore: Ø22 → Ø26" and be understood by the user, the CAD agent and the next spec.

**Why no references to fillets or generated edges.** These faces disappear or get renumbered when the feature that made them changes. A sketch placed on a fillet face is the most common reason a parametric model fails after an edit. The research backs this up: selecting geometry by index or by generated topology is brittle ([prompt-research.md](prompt-research.md), CADIR).

## 5. Change tracking

**Rule:** specs are numbered `v1`, `v2`… After a build, a change produces a delta spec: what parameters changed, which features they affect, and for each feature whether it's an edit or a rebuild. EXPECT is updated with it.

**Why a delta.** Rebuilding the whole part for one changed number throws away the feature tree and anything the user did by hand in the CAD program. A delta tells the CAD agent exactly which values to edit. Marking each change as **edit** (same features, new value) or **rebuild** (the topology changes, e.g. 4 holes become 6) tells it when a plain edit isn't enough.

**Why update EXPECT.** The build check (bounding box, feature and hole counts) is what caught real errors in [test run 1](test-run-1.md). Without a new EXPECT, every iteration after the first goes unchecked.

## 6. Housekeeping

**Rules:** units mm; a material in every spec; file names `<project>-<part>-v<n>`.

**Why.** A fixed unit removes the most common silent error (mm vs. inches vs. cm). Material drives mass, the process checks and whether a wall is thick enough, so a part without one can't be fully checked. File names that match spec versions make it obvious which file a delta applies to.

## What was left out

- **A fixed global coordinate system for whole assemblies.** Assemblies are out of scope for now (see SKILL.md, Ceiling). Interface-based origins (rule 3) get most of the benefit without it.
- **Configurations and design tables.** Useful for families of parts, but they are CAD-specific and the delta spec covers the single-part iteration case.
- **Automatic tolerance stacks.** Worth doing once assemblies are in scope; today the skill only names fits per feature.
