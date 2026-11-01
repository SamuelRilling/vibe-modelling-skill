# Build spec format

**In short:** the build spec is the plain-text handoff from the skill to whatever builds the part: a CAD agent, an MCP server, or a person. It is a header block (part, orientation, origin, parameters), a numbered feature list where every feature states what, size, where and how far, and an EXPECT line the builder checks its result against. After a change, a short delta spec says what to edit. It doesn't depend on any one CAD program.

Examples: [motor-plate-v1](../examples/motor-plate-v1.txt), [bushing-v1](../examples/bushing-v1.txt), [motor-plate-v2 delta](../examples/motor-plate-v2.delta.txt). Check a spec with `python skills/vibe-modelling-skill/scripts/lint_spec.py <file>`.

## Why this shape

- **Not prose:** "a plate with a few holes near the corners" has many valid readings. The builder would have to guess.
- **Not code:** a SolidWorks macro or an Onshape FeatureScript ties the spec to one program and hides intent behind API calls.
- **Not bare coordinates:** "hole at (42, 22)" builds once, but the model loses why it is there, so changing the plate width breaks it.
- **A structured feature list** sits between them: exact enough to build without guessing, readable by a person, and portable. Research on text-to-CAD points the same way: an intermediate representation with named features and relations beats raw code, and selecting geometry by index is the most fragile part ([prompt-research.md](prompt-research.md)).

## Full spec

```
PART: <name> v<n> · <material>, <process> · units mm · file <project>-<name>-v<n>
ORIENTATION: up = <what up means for this part>; front = <which side faces front>
DATUM: origin <where, relative to the interface>; <symmetry>
PARAMETERS: <name>=<value or relation> ...

1. <Name>: <operation and size> · <where> · <how far>
2. ...

EXPECT: <bbox> · <hole / feature counts> · <key dimensions> · <volume, optional>
```

### Header lines

| Line | Required content | Notes |
|---|---|---|
| `PART` | name, version right after it (`motor-plate v1`), material and process, `units mm` | file name follows `<project>-<part>-v<n>` |
| `ORIENTATION` | what "up" and "front" mean physically | up = top-plane normal, see [conventions](conventions.md#1-orientation) |
| `DATUM` | where the origin is and why, symmetry planes | origin on the mating interface, see [conventions](conventions.md#2-origin) |
| `PARAMETERS` | `name=value` pairs, separated by spaces | values may be relations (`hx=L/2−inset`); annotations in brackets after a value are allowed (`hole_d=5.5 (M5)`) |
| `EXPECT` | what the builder can measure | bounding box (width × height × depth, height along up), counts, key sizes, volume if computed |

### Feature lines

`<n>. <Name>: <slot> · <slot> · <slot>`, numbered from 1, in build order. Slots are separated by ` · ` (a middle dot with spaces). Lines indented below a feature continue it.

The four slots:

| Slot | Says | Examples |
|---|---|---|
| **what** + **size** | operation and its size | `extrude`, `cut Ø bore_d`, `hole Ø hole_d`, `revolve 360°`, `fillet R r`, `chamfer ch × 45°` |
| **where** | the sketch plane or face, and the position from a datum or another feature | `sketch on top plane: rectangle L × W centered on origin`, `on top face of Base`, `concentric with origin`, `4×, centers at (±hx, ±hy)` |
| **how far** | end condition and direction | `blind T, upward`, `through all`, `up to top face of Body`, `mid-plane 10` |

Fillets and chamfers have no "how far": `what · which edges` is complete.

### Rules

- **Names by role:** every feature gets a name that says what it is for (`Mount holes`, `Bearing seat`). Later steps and deltas refer to it by that name.
- **Planes by role:** `top plane`, `front plane`, `right plane`. Never a localized name (`Planta`) or a generated one (`Plane1`).
- **Faces and edges by feature + description:** `top face of Base`, `4 vertical edges of Base`. Never by index (`Face2`, `Edge14`), and never a face created by a fillet or chamfer.
- **Sketch axes:** coordinates inside a sketch are in that sketch plane's own (x, y). The first time a plane is used, state how its axes map to the model (`front plane: sketch x = model X, sketch y = up`). Don't mix sketch and model coordinates in one feature.
- **Relations next to numbers:** write computed positions out, with the relation beside them (`(±hx, ±hy) = (±42, ±22)`), so the builder doesn't have to compute and the intent survives.
- **Every value** has units or comes from PARAMETERS. Every parameter is used.
- **Order:** base body → main cuts and bosses → holes → patterns → fillets and chamfers.

## Delta spec

After a part is built, changes go out as a delta, not a new full spec:

```
DELTA: <name> v<n> → v<n+1>
CHANGED: <parameter> <old> → <new> · ...
AFFECTED: <n>. <Name> (<edit | rebuild | none>: <what>) · ...
EXPECT: <updated checks>
```

- **edit**: same features, a value changes. The builder edits the dimension in place.
- **rebuild**: the topology changes (4 holes become 6, a pocket becomes a slot). The builder deletes and recreates that feature, and every feature after it that referenced it.
- **none**: listed so the builder knows it was considered, e.g. a through-all cut that follows the new thickness on its own.

## For builder authors

What a builder (CAD agent or MCP server) should do with a spec:

1. Map the roles to its own CAD program: top / front / right planes, "up" as the top-plane normal.
2. Create PARAMETERS as driving variables (SolidWorks global variables or equations, Onshape variables, Fusion user parameters) when it can; otherwise substitute the values.
3. Build the features in order, naming each one as the spec does.
4. Measure the result and compare it with EXPECT; report any difference instead of hiding it.
5. For a delta, apply only the listed edits and rebuilds, then check the new EXPECT.

[sw_mcp](https://github.com/tylerstoltz/sw_mcp) for SolidWorks is one builder this has been tested with ([test-run-1.md](test-run-1.md)).
