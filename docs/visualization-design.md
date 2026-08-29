# Visualization design

The visualization is intentionally **static in layout, interactive in inspection**.

The previous implementation used Kamada–Kawai by default and exposed a spring-layout redraw button. That made the same argument graph move between renders even though the argument semantics had not changed. It also encoded the selected argument by parsing Plotly hover HTML in the callback.

The current design keeps graph geometry deterministic and uses interaction only to inspect a node.

## Main argument map

The map uses a layered Sugiyama layout computed by `python-igraph`, which is already part of the project.

For layout purposes, attack edges are reversed so the focused argument is placed first:

```text
focused argument
      ↓
   attackers
      ↓
counter-attackers
```

The visible red arrows still point in the real semantic direction:

```text
attacker ─────→ attacked argument
```

This makes depth meaningful and removes physics-based motion.

Argument semantics are not treated as mutually exclusive. An argument may be both **Grounded** and **Ideal**; the detail view preserves both labels. **Admissible** is shown when neither stronger status applies, and otherwise the argument is shown as **Not accepted**.

Clicking a card changes the explanation panel but does not change map geometry.

## Dialogical explanation

The reasoning engine still generates dispute trees. The visualization then performs a presentation-only reduction before layout:

- each generated dispute tree remains a separate component;
- equivalent states are merged only when they occur at the same depth in the same component;
- multiple incoming paths are preserved;
- equivalent states at different depths are not merged.

The displayed result is therefore a layered **DAG view of the generated dispute tree**, not a change to the underlying argumentation algorithm. Shared states are marked with the number of equivalent paths they represent.

Proponent, opponent, and terminal states remain visually distinct, and acceptance results are shown as explicit status pills instead of annotations floating inside the graph.

## Derivation

Selecting an argument also exposes its minimal premise sets. When premise sets exist, the first one is selected automatically so the natural-deduction explanation is immediately visible. Other premise sets remain selectable when alternatives exist.

## Repository survey

Several current or domain-specific projects informed the redesign.

### Argdown

https://github.com/argdown/argdown

Useful idea: stable argument maps are a communication artifact, not a physics simulation. Argdown supports Graphviz-backed exports and explicitly treats reduction of visual complexity as a core concern.

Adapted here:

- deterministic hierarchy;
- compact argument cards;
- semantic relations visible without animation;
- export-friendly geometry.

### Debate Map

https://github.com/debate-map/app

Useful idea: claims and support/oppose relations should be readable before opening detail. The map is navigation over reasoning, not merely a network diagram.

Adapted here:

- short claim summaries on the map;
- red attack semantics;
- detail-on-selection rather than detail-only-on-hover.

### OVA3

https://github.com/arg-tech/OVA3

Useful idea: keep the argument model separate from drawing. OVA3 has a distinct model and SVG drawing layer.

Adapted here:

- graph layout and presentation no longer determine how an argument is identified;
- callbacks use the argument ID carried in `customdata`, not text scraped from the rendered label.

### React Flow

https://github.com/xyflow/xyflow

React Flow is a strong choice for node editors and highly interactive diagram applications. It was not adopted because NDSA is currently a read-only research viewer. Adding a React build solely for rendering would introduce a second application stack without providing editing semantics the project needs.

Reconsider React Flow if NDSA gains:

- direct graph editing;
- drag-to-create relations;
- custom node forms;
- collaborative canvas state.

### AntV G6

https://github.com/antvis/G6

G6 is attractive for large interactive graph applications and offers rich layouts and rendering backends. It was not adopted for the same reason as React Flow: the current dataset is small and the project does not need a separate JavaScript graph runtime.

Reconsider G6 if the argument graph grows to thousands of elements or requires graph-analysis interactions in the browser.

### ELK / elkjs

https://github.com/kieler/elkjs

ELK's layered layout is conceptually a very good match for argument graphs. The current implementation uses igraph's Sugiyama layout instead because it provides the same important property—stable layered geometry—without adding a Node/JS layout dependency.

Reconsider ELK if future graphs require ports, compound nodes, or more advanced edge routing.

## Validation strategy

The repository now has CI for both data/figure behavior and browser rendering:

- every selectable claim is rendered twice and checked for deterministic argument-map positions;
- extension serialization is round-tripped;
- overlapping Grounded/Ideal semantics are covered by a regression test;
- the default dispute explanation is checked to ensure equivalent states are actually collapsed;
- a real Dash server is opened in Chromium and both Plotly views, selected argument detail, and default derivation must render without page or console errors;
- the browser run uploads a full-page screenshot and logs for visual inspection.

## Deliberate non-goals

This pass does not:

- turn the map into an editor;
- animate layout changes;
- migrate the Python application to React;
- change the argumentation engine;
- change the underlying debate knowledge base;
- combine the visualization redesign with a Dash/Plotly major-version migration.

Those are separate architectural decisions and should not be coupled to visual modernization.
