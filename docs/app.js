const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  data: null,
  claim: null,
  selectedNodeId: 0,
  rotation: 0,
};

const $ = (selector) => document.querySelector(selector);

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shorten(value, limit = 54) {
  return value.length <= limit ? value : `${value.slice(0, limit - 1)}…`;
}

function addArrowMarker(svg, id) {
  const defs = svgElement("defs");
  const marker = svgElement("marker", {
    id,
    viewBox: "0 0 10 10",
    refX: 9,
    refY: 5,
    markerWidth: 7,
    markerHeight: 7,
    orient: "auto-start-reverse",
  });
  marker.appendChild(svgElement("path", { d: "M 0 0 L 10 5 L 0 10 z" }));
  defs.appendChild(marker);
  svg.appendChild(defs);
}

function graphPositions(nodes) {
  const center = { x: 450, y: 270 };
  const radiusX = 300;
  const radiusY = 190;
  return new Map(
    nodes.map((node, index) => {
      const angle = state.rotation - Math.PI / 2 + (index * Math.PI * 2) / nodes.length;
      return [
        node.id,
        {
          x: center.x + Math.cos(angle) * radiusX,
          y: center.y + Math.sin(angle) * radiusY,
        },
      ];
    }),
  );
}

function trimmedLine(source, target, padding = 38) {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const length = Math.hypot(dx, dy) || 1;
  const ux = dx / length;
  const uy = dy / length;
  return {
    x1: source.x + ux * padding,
    y1: source.y + uy * padding,
    x2: target.x - ux * padding,
    y2: target.y - uy * padding,
  };
}

function renderArgumentGraph() {
  const svg = $("#argument-graph");
  svg.replaceChildren();
  addArrowMarker(svg, "attack-arrow");

  const positions = graphPositions(state.claim.nodes);

  for (const edge of state.claim.edges) {
    const line = trimmedLine(positions.get(edge.source), positions.get(edge.target));
    svg.appendChild(
      svgElement("line", {
        ...line,
        class: "attack-edge",
        "marker-end": "url(#attack-arrow)",
      }),
    );
  }

  for (const node of state.claim.nodes) {
    const position = positions.get(node.id);
    const group = svgElement("g", {
      class: `argument-node${node.id === state.selectedNodeId ? " is-selected" : ""}`,
      transform: `translate(${position.x} ${position.y})`,
      tabindex: 0,
      role: "button",
      "aria-label": `${node.label}: ${node.conclusionText}`,
    });

    const title = svgElement("title");
    title.textContent = `${node.raw}\n${node.conclusionText}`;
    group.appendChild(title);
    group.appendChild(svgElement("circle", { r: 35 }));

    const label = svgElement("text", { y: 5, "text-anchor": "middle" });
    label.textContent = node.label;
    group.appendChild(label);

    const select = () => selectNode(node.id);
    group.addEventListener("click", select);
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select();
      }
    });
    svg.appendChild(group);
  }

  $("#graph-summary").textContent = `${state.claim.nodes.length} arguments · ${state.claim.edges.length} attacks`;
}

function buildDisputeEntries(rootId, maxDepth = 3) {
  const entries = [];
  let serial = 0;

  function visit(id, depth, parentKey, path) {
    const key = `tree-${serial++}`;
    const cycle = path.has(id);
    entries.push({ key, id, depth, parentKey, cycle });
    if (cycle || depth >= maxDepth) return;

    const nextPath = new Set(path);
    nextPath.add(id);
    const attackers = state.claim.edges
      .filter((edge) => edge.target === id)
      .map((edge) => edge.source);

    for (const attacker of attackers) {
      visit(attacker, depth + 1, key, nextPath);
    }
  }

  visit(rootId, 0, null, new Set());
  return entries;
}

function renderDisputeTree() {
  const svg = $("#dispute-tree");
  svg.replaceChildren();
  addArrowMarker(svg, "tree-arrow");

  const entries = buildDisputeEntries(state.selectedNodeId);
  const levels = new Map();
  for (const entry of entries) {
    if (!levels.has(entry.depth)) levels.set(entry.depth, []);
    levels.get(entry.depth).push(entry);
  }

  const tallestLevel = Math.max(...[...levels.values()].map((level) => level.length));
  const height = Math.max(320, tallestLevel * 86 + 60);
  svg.setAttribute("viewBox", `0 0 940 ${height}`);

  const positions = new Map();
  for (const [depth, level] of levels) {
    const gap = height / (level.length + 1);
    level.forEach((entry, index) => {
      positions.set(entry.key, {
        x: 820 - depth * 235,
        y: gap * (index + 1),
      });
    });
  }

  for (const entry of entries) {
    if (!entry.parentKey) continue;
    const source = positions.get(entry.key);
    const target = positions.get(entry.parentKey);
    svg.appendChild(
      svgElement("line", {
        x1: source.x + 82,
        y1: source.y,
        x2: target.x - 82,
        y2: target.y,
        class: "tree-edge",
        "marker-end": "url(#tree-arrow)",
      }),
    );
  }

  for (const entry of entries) {
    const node = state.claim.nodes.find((candidate) => candidate.id === entry.id);
    const position = positions.get(entry.key);
    const group = svgElement("g", {
      class: `tree-node${entry.depth === 0 ? " is-root" : ""}${entry.cycle ? " is-cycle" : ""}`,
      transform: `translate(${position.x} ${position.y})`,
    });
    group.appendChild(svgElement("rect", { x: -82, y: -30, width: 164, height: 60, rx: 4 }));

    const label = svgElement("text", { x: -68, y: -7 });
    label.textContent = `${node.label} · ${node.conclusion}`;
    group.appendChild(label);

    const summary = svgElement("text", { x: -68, y: 13, class: "tree-summary" });
    summary.textContent = entry.cycle ? "cycle stops here" : shorten(node.conclusionText, 31);
    group.appendChild(summary);
    svg.appendChild(group);
  }

  $("#tree-summary").textContent = "Attackers expand from right to left; repeated cycles stop after first re-entry.";
}

function renderPremiseSet(index) {
  const node = state.claim.nodes.find((candidate) => candidate.id === state.selectedNodeId);
  const premiseSet = node.premiseSets[index];

  $("#selected-premises").innerHTML = premiseSet.formulas
    .map(
      (formula, premiseIndex) => `
        <li>
          <code>${escapeHtml(formula)}</code>
          <span>${escapeHtml(premiseSet.descriptions[premiseIndex])}</span>
        </li>`,
    )
    .join("");

  $("#selected-claim").innerHTML = `
    <code>${escapeHtml(node.conclusion)}</code>
    <span>${escapeHtml(node.conclusionText)}</span>`;

  const premiseSentences = premiseSet.descriptions
    .map((description) => `<li>${escapeHtml(description)}.</li>`)
    .join("");
  $("#explanation").innerHTML = `
    <p class="explanation-lead">For this stored derivation, take the following premises:</p>
    <ol>${premiseSentences}</ol>
    <p class="therefore"><span>Therefore</span> ${escapeHtml(node.conclusionText)}.</p>`;
}

function renderNodeDetails() {
  const node = state.claim.nodes.find((candidate) => candidate.id === state.selectedNodeId);
  $("#selected-argument-label").textContent = node.label;
  $("#selected-argument-formula").textContent = node.raw;
  $("#selected-argument-summary").textContent = node.conclusionText;

  const select = $("#premise-select");
  select.replaceChildren();
  node.premiseSets.forEach((premiseSet, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `Set ${index + 1} — ${premiseSet.formulas.length} premise${premiseSet.formulas.length === 1 ? "" : "s"}`;
    select.appendChild(option);
  });
  select.onchange = () => renderPremiseSet(Number(select.value));
  renderPremiseSet(0);
}

function selectNode(nodeId) {
  state.selectedNodeId = nodeId;
  renderArgumentGraph();
  renderDisputeTree();
  renderNodeDetails();
}

function selectClaim(claimId) {
  state.claim = state.data.claims.find((claim) => claim.id === claimId);
  state.selectedNodeId = state.claim.nodes[0].id;
  state.rotation = 0;
  renderArgumentGraph();
  renderDisputeTree();
  renderNodeDetails();
}

async function boot() {
  try {
    const response = await fetch("./data.json");
    if (!response.ok) throw new Error(`Unable to load data.json (${response.status})`);
    state.data = await response.json();

    $("#research-question").textContent = state.data.title;
    const claimSelect = $("#claim-select");
    for (const claim of state.data.claims) {
      const option = document.createElement("option");
      option.value = claim.id;
      option.textContent = claim.label;
      claimSelect.appendChild(option);
    }
    claimSelect.addEventListener("change", () => selectClaim(claimSelect.value));

    $("#redraw-button").addEventListener("click", () => {
      state.rotation += Math.PI / 8;
      renderArgumentGraph();
    });

    selectClaim(state.data.claims[0].id);
    $("#app-status").hidden = true;
  } catch (error) {
    $("#app-status").textContent = error.message;
    $("#app-status").classList.add("is-error");
  }
}

boot();
