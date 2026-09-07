# CoreForge — contributor and agent guide

For humans and for coding agents. `CLAUDE.md` symlinks here so Claude Code picks
it up; other tools read `AGENTS.md` directly.

`README.md` covers installing and running the tooling. This file covers the
design: what the pieces are, which invariants will bite you if you do not know
them, and how to add a geometry element, a builder, or a whole physics code.

Most of what follows is a description of decisions already made in the code, not
new policy. Where something is genuinely undecided it is in **Open questions**
at the bottom, phrased as a question.

---

## What CoreForge is

A **code-agnostic description of a reactor**, plus **per-physics-code builders**
that render it.

```
coreforge/
  geometry_elements/   what the reactor is: pincells, lattices, stacks, blocks
  materials/           what it is made of, with citations
  shapes/              the primitives geometry elements are composed from
  openmc_builder/      render a geometry element to OpenMC
  mpact_builder/       render the same element to MPACT
```

The whole contract is 50 lines in `geometry_elements/geometry_element.py`: a
name, `__eq__`, `__hash__`, and `get_materials()`. Everything else is rendering.

One reactor described once, rendered to two codes, is the property worth
protecting. A change that makes a geometry element easier to build for one code
at the cost of that property is the wrong trade.

## What CoreForge is not

- **Not a runner.** It returns an `openmc.Universe` or an `mpactpy.Core`.
  Settings, tallies, cross sections, execution and statepoint parsing belong to
  whatever runs the model.
- **Not a service.** It is a pip-installable library. No daemon, no HTTP, no
  database session.
- **Not generic.** `Core.RING_MAP` hardcodes the NETL positions and
  `RESERVED_LOCATIONS` hardcodes the rod locations because that is what the
  docketed safety analysis says. Generalising that costs fidelity and buys
  nothing.

---

## How builders are found

Both builder packages keep a registry and dispatch by walking the element's
class chain:

```python
cls = type(element)
while cls is not object:
    builder_cls = _builder_registry.get(cls)
    if builder_cls:
        return builder_cls
    cls = cls.__base__
```

This is the design decision most worth understanding. A facility-specific
subclass inherits its parent's builder for free — you subclass `PinCell` for a
particular reactor and it renders without writing anything. Register a builder
only when the rendering genuinely differs.

Note it walks `__base__`, not the full method resolution order, so **the
dispatch follows single inheritance**. A geometry element that picks up its
buildable identity from a second base class will not be found.

---

## Invariants that will bite you

### Equality and hashing are tolerance-aware, together

`Material.__eq__` compares density, temperature and number densities with
`isclose(rel_tol=TOL)`, where `TOL` is `ROUNDING_RELATIVE_TOLERANCE = 1E-5` from
`mpactpy.utils`. `__hash__` uses `relative_round(..., TOL)` on the same fields.

The two must stay consistent. If you add a field to equality, round it the same
way in the hash, or you get objects that compare equal and hash differently —
which silently breaks every de-duplication path, including `unique_materials`
and the lattice de-duplication the MPACT build depends on. That is not a
crash; it is an MPACT model with ninety unique lattices where twelve were
intended.

### One name, one composition

`unique_materials` raises `ValueError` when two materials share a name and
differ in composition. That guard is the reason a reactor cannot quietly contain
two different definitions of the same fuel. Preserve it in anything that
collects or merges materials.

### Units are fixed and unlabelled

Centimetres, grams per cubic centimetre, Kelvin, degrees. Inputs are often in
inches — convert at the human-facing layer (`CM_PER_INCH`) and store canonical
units. A per-value `units` field would be an invitation to mix them.

### Geometry and mesh are different documents

`VoxelationSpecs`, `CoreCellSpecs.unionize_radial_mesh` and
`Stack.Segment.Specs.target_axial_thickness` are **meshing** decisions — per
code, per study. The same reactor with a different mesh is a different *run*,
not a different reactor. Keep the two separable, or someone will diff a
multiplication factor across a mesh change and call it a geometry change.

### Some parameters are semantics, not formatting

`FuelElement.gap_tolerance` defaults to `1.0e-8` and *removes geometry* thinner
than that. It looks like a rounding detail and it changes the model.

### Hexagonal maps have two spellings and an orientation

`HexLattice` accepts `map_type='offset'` (what a person draws) or `'ring'` (what
is stored, after `offset_to_ring`), and `orientation` decides which physical
position index zero is. Get the orientation wrong and you have rotated the core
by thirty degrees, which runs fine and gives a different flux tilt.

---

## Adding things

### A geometry element

1. Subclass `GeometryElement` in `geometry_elements/`.
2. Implement `__eq__`, `__hash__` and `get_materials()`. Follow the tolerance
   rule above — compare with `isclose(rel_tol=TOL)`, hash with
   `relative_round`.
3. Validate in the constructor. `PinCell._set_zones` asserting that zone
   boundaries cannot intersect is the model: a physically impossible object
   should be impossible to construct, not merely wrong later.
4. Add tests under `test/unit/` mirroring the module path.

### A builder for an existing code

```python
@register_builder(geometry_elements_triga.FuelElement)
class FuelElement(Builder[geometry_elements_triga.FuelElement]):
    def build(self, element): ...
```

Register only when rendering differs from the parent's. Inheritance already
covers the common case.

### A new physics code

A code is onboarded when it has all of these, and not before:

1. **A builder package** — `<code>_builder/` with its own registry and the same
   `register_builder` / `get_builder` / `build` trio, so there is one idiom
   across the repository.
2. **Builders for the existing element vocabulary**, so an existing reactor
   renders to the new code without being re-described.
3. **A worked reactor** under `test/unit/`, ideally one that already exists for
   another code, so the two renderings can be compared.

A **systems thermal-hydraulics code does not fit the current vocabulary.** Its
models are loops, junctions, pipes and heat structures, not pin cells and
lattices. There is no honest common supertype with core geometry. The right
shape for such a code is a sibling element family that shares the
declare-and-dispatch pattern, not a forced fit into `geometry_elements/`.

---

## Conventions

- **Docstrings are numpy-style** with a leading space after `"""`, matching the
  existing modules. Parameters and Returns sections on anything public.
- **Cite physical data.** `materials/uzrh.py` carries a DOI and page numbers for
  its composition and density; `geometry_elements/triga/netl/core.py` cites the
  docketed source for the core map. A number without a citation is a number
  nobody can check. This is the most valuable property in the repository.
- **Tests mirror the package path** under `test/unit/`.
- **CI runs `pytest test/unit/` and `pylint ./coreforge`.** Lint must be clean;
  the disabled-message list lives in `pyproject.toml`.
- **Keep the dependency list short.** It is currently numpy, openmc and MPACTPy.
  Each addition is a constraint on everywhere CoreForge can be installed.

---

## Open questions

Genuinely undecided, listed so a newcomer does not mistake them for settled.

**Should the spec serialise?** There is no `to_dict`, `from_dict`, schema, YAML
or JSON anywhere. A model is a Python program, so it cannot be archived,
diffed, or handed to anything that is not a Python process holding the same
imports — the as-built core loading currently lives in a test fixture. If this
is taken up, the acceptance criterion that matters is
`from_dict(to_dict(x)) == x` under the existing tolerance-aware equality, over
every class in `geometry_elements/`, with geometry and mesh specs as separate
documents. The traps are listed under **Invariants** above; content-addressing
shared materials and restoring identity by hash rather than by name is the
non-obvious one.

**Should `Material` keep storing its data in an OpenMC object?**
`Material.__init__` takes an `openmc.Material` and the code-agnostic properties
delegate to it, which means composition cannot be stated or read without OpenMC
installed. There is a real argument for the status quo — `Graphite` is a
*calculation* (theoretical density, boron-equivalent contamination, pore
intrusion, then `mix_materials`), and OpenMC does the isotopic and
natural-abundance expansion that reimplementing would mean reimplementing a
nuclear data library. The narrower question is whether `Material` should be able
to *emit* a composition record without OpenMC in the process, while keeping
OpenMC as the computational engine.

**Should the physics codes be optional extras?** Both are hard dependencies
today, so building an MPACT model requires OpenMC installed, and adding a fourth
code would drag along the other three.

---

_Copyright (c) 2026 The University of Texas at Austin. BSD-3-Clause licensed._
