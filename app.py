import ast
import copy
import io
import json
import re
import textwrap
from contextlib import redirect_stdout
from pathlib import Path

import dash
from dash import dash_table, dcc, html
import igraph
import pandas as pd
import plotly.graph_objects as go

from argument_engine.argument import Extensions, FindArgument
from argument_engine.natural_deduction import NaturalDeduction

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_PATH = DATA_DIR / "debate_kb.csv"
CACHE_EXTENSION_PATH = DATA_DIR / "cache_ext.txt"
CACHE_PREMISES_PATH = DATA_DIR / "cache_premises.txt"

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server
app.title = "NDSA Debate Visualization"

title = pd.read_csv(KB_PATH, nrows=1, header=None)
df = pd.read_csv(KB_PATH, header=1)

STATUS_STYLE = {
    "grounded": {"fill": "#eaf7f0", "border": "#247a52", "label": "Grounded"},
    "ideal": {"fill": "#eef3ff", "border": "#4464ad", "label": "Ideal"},
    "admissible": {"fill": "#fff7e6", "border": "#ad6b00", "label": "Admissible"},
    "not accepted": {"fill": "#f2f4f7", "border": "#667085", "label": "Not accepted"},
}

TREE_STATUS_COPY = {
    "not a dispute tree": "Not accepted — the proponent cannot defend against an opponent.",
    "not admissible": "Not admissible — an argument is used by both sides.",
    "admissible": "Admissible — the proponent can defend against every attack in this tree.",
    "grounded": "Grounded — the defence terminates.",
    "ideal": "Ideal — opponents do not have an admissible counter-position.",
    "grounded,ideal": "Grounded and ideal — the defence terminates and opponents lack an admissible counter-position.",
}


def update_options():
    options = []
    for item in df.itertuples():
        if item.number.startswith("T"):
            prefix = "Trump"
        elif item.number.startswith("B"):
            prefix = "Biden"
        elif item.number.startswith("C"):
            prefix = "Conclusion"
        elif item.number.startswith("N"):
            continue
        else:
            continue
        options.append({"label": f"{prefix} · {item.proof}", "value": item.proposition})
    return options


def _restore_extension(raw_extension):
    dumped = ast.literal_eval(raw_extension.replace("set()", '"empty_set"'))
    for key, value in dumped.items():
        if isinstance(value, list):
            dumped[key] = [set() if item == "empty_set" else item for item in value]
        elif value == "empty_set":
            dumped[key] = set()
    extension = Extensions.__new__(Extensions)
    extension.__dict__.update(dumped)
    return extension


def _serialize_extension(extension):
    return str(extension.__dict__.copy())


def load_argument_state(claim):
    try:
        with CACHE_EXTENSION_PATH.open(encoding="utf-8") as cache_file:
            extension_cache = json.load(cache_file)
        extension = _restore_extension(extension_cache[claim])

        with CACHE_PREMISES_PATH.open(encoding="utf-8") as cache_file:
            premises_cache = json.load(cache_file)
        separated_premises = premises_cache[claim]
    except (FileNotFoundError, KeyError, ValueError, SyntaxError):
        knowledge_base = copy.deepcopy(df)
        arguments, relation, separated_premises = FindArgument(knowledge_base).find_all(claim, combine=True)
        extension = Extensions(arguments, relation)

    return extension, separated_premises


def argument_status(extension, node):
    if node in extension.grounded:
        return "grounded"
    if node in extension.ideal:
        return "ideal"
    if any(node in candidate for candidate in extension.admissible):
        return "admissible"
    return "not accepted"


def strip_markup(value):
    return re.sub(r"<[^>]+>", "", value or "")


def wrap_label(value, width=30, max_lines=3):
    clean = " ".join(strip_markup(value).split())
    lines = textwrap.wrap(clean, width=width) or [clean]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    return "<br>".join(lines)


def get_claim_text(claim_str):
    claim = df.loc[df["proposition"] == str(claim_str)]
    if claim.empty:
        claim, number_of_not = deal_with_not(str(claim_str))
        text = "not that "
        while number_of_not > 1:
            text += "not that "
            number_of_not -= 1
        text += [item.proof for item in claim.itertuples()][0]
        return text
    return [item.proof for item in claim.itertuples()][0]


def generate_support_claim_text(dataframe, supports_list, claim_str=None):
    support_text = ""
    for prop in supports_list:
        support = dataframe.loc[dataframe["proposition"] == str(prop)]
        if support.empty:
            continue
        row = next(support.itertuples())
        single_text = row.proof
        if row.type.startswith("statement"):
            support_type = "Trump's statement" if row.speaker.startswith("D") else "Biden's statement"
        else:
            support_type = "assumption"
        support_text += f"<b>{support_type}</b>: {single_text[0].upper() + single_text[1:]}.<br><br>"

    if claim_str is not None:
        return support_text.removesuffix("<br><br>"), get_claim_text(claim_str)
    return support_text.removesuffix("<br><br>")


def _argument_data(extension, node):
    raw_premise, conclusion = re.findall(r"\{(.*)\}\|-(.+)", extension.original_arg[node])[0]
    premises = [] if raw_premise == "" else raw_premise.split(", ")
    support_text, claim_text = generate_support_claim_text(df, premises, conclusion)
    return premises, conclusion, support_text, claim_text


def _layered_positions(extension):
    count = len(extension.arguments)
    if count == 1:
        return {0: (0.0, 0.0)}, [0]

    layout_graph = igraph.Graph(directed=True)
    layout_graph.add_vertices(count)
    # Layout direction is intentionally reversed: focal argument -> attacker -> counter-attacker.
    layout_graph.add_edges([(attackee, attacker) for attacker, attackee in extension.relation])

    distances = layout_graph.distances(source=0, mode="out")[0]
    finite = [int(distance) for distance in distances if distance != float("inf")]
    fallback_layer = (max(finite) + 1) if finite else 1
    layers = [fallback_layer if distance == float("inf") else int(distance) for distance in distances]

    layout = layout_graph.layout_sugiyama(layers=layers, hgap=2.5, vgap=1.0, maxiter=200)
    positions = {}
    for node, coordinate in enumerate(layout):
        positions[node] = (float(coordinate[0]) * 3.4, -float(layers[node]) * 2.1)
    return positions, layers


def argument_graph(extension):
    positions, layers = _layered_positions(extension)
    fig = go.Figure()

    for attacker, attackee in extension.relation:
        x0, y0 = positions[attacker]
        x1, y1 = positions[attackee]
        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.15,
            arrowwidth=1.5,
            arrowcolor="#d92d20",
            opacity=0.55,
        )

    x_values = []
    y_values = []
    hover_values = []
    custom_data = []

    for node in extension.arguments:
        x, y = positions[node]
        _, _, support_text, claim_text = _argument_data(extension, node)
        status = argument_status(extension, node)
        style = STATUS_STYLE[status]

        x_values.append(x)
        y_values.append(y)
        custom_data.append([node])
        hover_values.append(
            f"<b>Argument A{node}</b><br>{strip_markup(claim_text)}"
            f"<br><br><b>Status</b>: {style['label']}"
            f"<br><br><b>Supported by</b><br>{support_text or 'No explicit premises'}"
        )

        fig.add_annotation(
            x=x,
            y=y,
            text=f"<b>A{node}</b><br>{wrap_label(claim_text)}",
            showarrow=False,
            align="left",
            bgcolor=style["fill"],
            bordercolor="#101828" if node == 0 else style["border"],
            borderwidth=2.5 if node == 0 else 1.4,
            borderpad=8,
            font={"size": 12, "color": "#101828"},
            width=220,
            captureevents=False,
        )

    # Transparent hit targets preserve selection while the visual layout stays static.
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="markers",
            marker={"size": 100, "color": "rgba(0,0,0,0.001)"},
            customdata=custom_data,
            hovertext=hover_values,
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        )
    )

    max_layer = max(layers) if layers else 0
    xs = list(positions[node][0] for node in positions)
    ys = list(positions[node][1] for node in positions)
    x_pad = 3.8
    y_pad = 1.3
    fig.update_layout(
        height=min(920, max(520, 180 * (max_layer + 1))),
        margin={"l": 30, "r": 30, "t": 20, "b": 30},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="closest",
        dragmode="pan",
        xaxis={
            "visible": False,
            "range": [min(xs) - x_pad, max(xs) + x_pad],
            "fixedrange": False,
        },
        yaxis={
            "visible": False,
            "range": [min(ys) - y_pad, max(ys) + y_pad],
            "fixedrange": False,
            "scaleanchor": None,
        },
        showlegend=False,
    )
    return fig


def dialogical_graph(extension, arg_number):
    edges, vertices, node_dict, arg_dict, root_dict = extension.dialogical_explanations(arg_number)
    if vertices == 0:
        return go.Figure(), []

    graph = igraph.Graph()
    graph.add_vertices(vertices)
    graph.add_edges(edges)
    layout = graph.layout("rt", root=[key for key in root_dict])
    positions = {node: (float(layout[node][0]) * 3.1, -float(layout[node][1]) * 2.0) for node in range(vertices)}

    fig = go.Figure()

    for source, target in edges:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.0,
            arrowwidth=1.2,
            arrowcolor="#98a2b3",
            opacity=0.75,
        )

    hover_x, hover_y, hover_text = [], [], []
    for node in range(vertices):
        label = node_dict.get(node, "")
        x, y = positions[node]

        if label.startswith("P"):
            role = "Proponent"
            fill = "#ecfdf3"
            border = "#2e8b57"
        elif label.startswith("O"):
            role = "Opponent"
            fill = "#fff4ed"
            border = "#c4320a"
        else:
            role = "Terminal state"
            fill = "#f2f4f7"
            border = "#667085"

        if arg_dict.get(node):
            match = re.findall(r"\{(.*)\}\|-(.+)", arg_dict[node])
            conclusion = match[0][1] if match else ""
            claim_text = get_claim_text(conclusion) if conclusion else label
            card_text = f"<b>{role} · {label.split(':')[-1].strip()}</b><br>{wrap_label(claim_text, 28, 2)}"
            hover = f"<b>{role}</b><br>{strip_markup(claim_text)}"
        else:
            card_text = f"<b>{role}</b><br>{wrap_label(label, 28, 3)}"
            hover = strip_markup(label)

        fig.add_annotation(
            x=x,
            y=y,
            text=card_text,
            showarrow=False,
            align="left",
            bgcolor=fill,
            bordercolor=border,
            borderwidth=1.3,
            borderpad=7,
            font={"size": 11, "color": "#101828"},
            width=205,
            captureevents=False,
        )
        hover_x.append(x)
        hover_y.append(y)
        hover_text.append(hover)

    fig.add_trace(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": 86, "color": "rgba(0,0,0,0.001)"},
            hovertext=hover_text,
            hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        )
    )

    xs = [positions[node][0] for node in positions]
    ys = [positions[node][1] for node in positions]
    depth = max((-positions[node][1] / 2.0 for node in positions), default=0)
    fig.update_layout(
        height=min(900, max(420, 175 * (int(depth) + 1))),
        margin={"l": 30, "r": 30, "t": 20, "b": 30},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis={"visible": False, "range": [min(xs) - 3.5, max(xs) + 3.5]},
        yaxis={"visible": False, "range": [min(ys) - 1.2, max(ys) + 1.2]},
        hovermode="closest",
        dragmode="pan",
        showlegend=False,
    )

    statuses = [TREE_STATUS_COPY.get(root_dict[key], root_dict[key]) for key in sorted(root_dict)]
    return fig, statuses


def build_argument_detail(extension, arg_number):
    premises, conclusion, _, claim_text = _argument_data(extension, arg_number)
    status = argument_status(extension, arg_number)
    status_style = STATUS_STYLE[status]
    premise_count = len(premises)
    return html.Div(
        [
            html.Div(
                [
                    html.Span(f"A{arg_number}", className="argument-id"),
                    html.Span(status_style["label"], className=f"status-pill status-{status.replace(' ', '-')}"),
                ],
                className="argument-detail-head",
            ),
            html.H3(strip_markup(claim_text), className="argument-detail-claim"),
            html.P(
                f"{premise_count} premise{'s' if premise_count != 1 else ''} · click another map card to inspect it",
                className="muted",
            ),
        ]
    )


def build_premise_options(separated_form, conclusion, claim_text):
    raw = separated_form.get(str(conclusion), "")
    premise_sets = re.findall(r"\{(.*?)\}", raw)
    options = []
    for index, item in enumerate(premise_sets, start=1):
        premises = [] if not item else item.split(", ")
        premise_html = generate_support_claim_text(df, premises)
        premise_text = strip_markup(premise_html.replace("<br>", "\n"))
        value = json.dumps(
            {
                "premises": premises,
                "conclusion": conclusion,
                "premises_text": premise_text,
                "claim_text": strip_markup(claim_text),
            }
        )
        count = len(premises)
        options.append(
            {
                "label": f"Premise set {index} · {count} premise{'s' if count != 1 else ''}",
                "title": premise_text,
                "value": value,
            }
        )
    return options


def deal_with_not(clause):
    number_of_not = 0
    add_not = False
    while True:
        if clause.startswith("~("):
            n_clause = clause[2:-1]
        elif clause.startswith("~"):
            n_clause = clause[1:]
        else:
            n_clause = "~" + clause if len(clause) == 1 else "~(" + clause + ")"
            add_not = True

        number_of_not += 1
        match = df.loc[df["proposition"] == n_clause]
        if not match.empty:
            break
        if add_not:
            raise ValueError(f"No proposition found for {clause}")
        clause = n_clause
    return match, number_of_not


def natural_language_transform(proof):
    nlp = ""
    proof_list = proof.split("\n")[:-1]
    prop_list = [""]
    index = 0

    while index < len(proof_list):
        prefix = re.search(r"[0-9]+\.[\s\|]+", proof_list[index])
        raw_prop = re.search(r"([^\w]|\b)([a-z\|\&\>\~\(\)])+", proof_list[index][prefix.end():])
        prop = raw_prop.group().strip(" ")
        match = df.loc[df["proposition"] == prop]
        if match.empty:
            raw_clause, number_of_not = deal_with_not(prop)
            clause = "__it is not the case that__ " * number_of_not
            clause += [item.proof for item in raw_clause.itertuples()][0]
        else:
            clause = [item.proof for item in match.itertuples()][0]

        prop_list.append(clause)

        if prefix.group().count("|") == 1:
            if "Premise" not in proof_list[index]:
                number = re.findall(r"[0-9]+", proof_list[index][prefix.end():])
                if len(number) == 1:
                    nlp += "__We have__ " + clause + ", __given that__ " + prop_list[int(number[0])] + ".\n\n"
                else:
                    nlp += "__We have__ " + clause + ", __given that__ "
                    nlp += " __and__ ".join([prop_list[int(item)] for item in number])
                    nlp += ".\n\n"
        else:
            if "RAA Assume" in proof_list[index]:
                while re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).group().count("|") != 1:
                    index += 1
                    prop_list.append("")

                if "Therefore" not in proof_list[index]:
                    raise ValueError("Malformed RAA proof")
                therefore = re.search(
                    r"([^\w]|\b)([a-z\|\&\>\~\(\)])+",
                    proof_list[index][re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).end():],
                ).group().strip(" ")
                str_therefore = _proof_clause_to_text(therefore)
                prop_list.append(str_therefore)
                nlp += (
                    "__If we assume that__ "
                    + clause
                    + ", __we will meet a contradiction. Therefore, we have__ "
                    + str_therefore
                    + ".\n\n"
                )

            elif "IfI Assume" in proof_list[index]:
                while re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).group().count("|") != 1:
                    index += 1
                    prop_list.append("")

                if "Therefore" not in proof_list[index]:
                    raise ValueError("Malformed implication-introduction proof")
                n_prefix = re.search(r"[0-9]+\.[\s\|]+", proof_list[index])
                therefore = re.search(
                    r"([^\w]|\b)([a-z\|\&\>\~\(\)])+",
                    proof_list[index][n_prefix.end():],
                ).group().strip(" ")
                str_therefore = _proof_clause_to_text(therefore)
                conclusion_number = int(re.findall(r"[0-9]+", proof_list[index][n_prefix.end():])[1])
                conclusion_if = re.search(
                    r"([^\w]|\b)([a-z\|\&\>\~\(\)])+",
                    proof_list[conclusion_number - 1][
                        re.search(r"[0-9]+\.[\s\|]+", proof_list[conclusion_number - 1]).end():
                    ],
                ).group().strip(" ")
                str_conclusion = _proof_clause_to_text(conclusion_if)
                nlp += (
                    "__If we assume that__ "
                    + clause
                    + ", __we will get__ "
                    + str_conclusion
                    + ". __Therefore, we have__ "
                    + str_therefore
                    + ".\n\n"
                )

            elif "Or Assume" in proof_list[index]:
                str_assume2 = ""
                while re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).group().count("|") != 1:
                    index += 1
                    if "Or Assume" in proof_list[index]:
                        assume2 = re.search(
                            r"([^\w]|\b)([a-z\|\&\>\~\(\)])+",
                            proof_list[index][re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).end():],
                        ).group().strip(" ")
                        str_assume2 = _proof_clause_to_text(assume2)
                        prop_list.append(str_assume2)
                    else:
                        prop_list.append("")

                if "Therefore" not in proof_list[index]:
                    raise ValueError("Malformed disjunction proof")
                therefore = re.search(
                    r"([^\w]|\b)([a-z\|\&\>\~\(\)])+",
                    proof_list[index][re.search(r"[0-9]+\.[\s\|]+", proof_list[index]).end():],
                ).group().strip(" ")
                str_therefore = _proof_clause_to_text(therefore)
                prop_list.append(str_therefore)
                nlp += (
                    "__We will get__ "
                    + str_therefore
                    + " __by assume either__ "
                    + clause
                    + " __or__ "
                    + str_assume2
                    + ". __Therefore, we have__ "
                    + str_therefore
                    + ".\n\n"
                )
            else:
                raise ValueError("Unsupported proof form")
        index += 1

    return nlp or "__The claim only supported by itself.__"


def _proof_clause_to_text(prop):
    match = df.loc[df["proposition"] == prop]
    if not match.empty:
        return [item.proof for item in match.itertuples()][0]

    raw_clause, number_of_not = deal_with_not(prop)
    text = "__it is not the case that__ " * number_of_not
    text += [item.proof for item in raw_clause.itertuples()][0]
    return text


GRAPH_CONFIG = {
    "displaylogo": False,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "scrollZoom": True,
    "responsive": True,
}


def legend():
    items = [
        ("Grounded", "legend-grounded"),
        ("Ideal", "legend-ideal"),
        ("Admissible", "legend-admissible"),
        ("Not accepted", "legend-not-accepted"),
        ("attacks", "legend-attack"),
    ]
    return html.Div(
        [
            html.Span([html.Span(className=f"legend-swatch {css}"), label], className="legend-item")
            for label, css in items
        ],
        className="legend",
    )


page1_layout = html.Div(
    [
        dcc.Store(id="extension"),
        html.Header(
            [
                html.Div(
                    [
                        html.P("NDSA · structured argumentation", className="eyebrow"),
                        html.H1("See the reasoning inside a debate"),
                        html.P(
                            "A stable argument map of claims, attacks, dispute trees, and formal derivations.",
                            className="lede",
                        ),
                    ]
                ),
                dcc.Link("Knowledge base", href="/use-case", className="secondary-link"),
            ],
            className="app-header",
        ),
        html.Main(
            [
                html.Section(
                    [
                        html.Div(
                            [
                                html.Label("Focus claim", htmlFor="candidate-dropdown", className="control-label"),
                                dcc.Dropdown(
                                    id="candidate-dropdown",
                                    placeholder="Select a claim",
                                    options=update_options(),
                                    optionHeight=72,
                                    multi=False,
                                    value="~a>~d",
                                    className="claim-select",
                                    clearable=False,
                                ),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.P("Debate", className="meta-label"),
                                html.P("Biden vs. Trump · second 2020 presidential debate", className="meta-value"),
                                html.P(title.values[0][0], className="meta-question"),
                            ],
                            className="debate-meta",
                        ),
                    ],
                    className="control-card",
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P("01", className="section-index"),
                                        html.Div(
                                            [
                                                html.H2("Argument map"),
                                                html.P(
                                                    "Fixed layered positions: focal argument → attackers → counter-attackers. Red arrows point from attacker to target.",
                                                    className="section-copy",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="section-title-row",
                                ),
                                legend(),
                            ],
                            className="section-heading",
                        ),
                        dcc.Loading(
                            type="circle",
                            children=dcc.Graph(id="main-graph", config=GRAPH_CONFIG, className="graph"),
                        ),
                    ],
                    className="panel",
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.P("02", className="section-index"),
                                html.Div(
                                    [
                                        html.H2("Selected argument"),
                                        html.P(
                                            "Selection changes explanation, not graph geometry.",
                                            className="section-copy",
                                        ),
                                    ]
                                ),
                            ],
                            className="section-title-row",
                        ),
                        html.Div(id="argument-detail", className="argument-detail"),
                        html.Div(id="dialogical-status", className="tree-status"),
                        dcc.Loading(
                            type="circle",
                            children=dcc.Graph(id="dialogical", config=GRAPH_CONFIG, className="graph"),
                        ),
                    ],
                    className="panel",
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.P("03", className="section-index"),
                                html.Div(
                                    [
                                        html.H2("Derivation"),
                                        html.P(
                                            "Choose one minimal premise set to inspect the natural-deduction proof.",
                                            className="section-copy",
                                        ),
                                    ]
                                ),
                            ],
                            className="section-title-row",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Premise set", htmlFor="premises-dropdown", className="control-label"),
                                        dcc.Dropdown(
                                            id="premises-dropdown",
                                            placeholder="Select a premise set",
                                            multi=False,
                                            className="claim-select",
                                        ),
                                        html.Div(
                                            [
                                                html.P("Premises", className="meta-label"),
                                                html.Pre(id="selected-premises", className="proof-box"),
                                                html.P("Claim", className="meta-label"),
                                                html.Pre(id="claim", className="proof-box"),
                                            ],
                                            className="proof-inputs",
                                        ),
                                    ],
                                    className="proof-column",
                                ),
                                html.Div(
                                    [
                                        html.P("Natural-language proof", className="meta-label"),
                                        html.Div(id="NLP", className="nlp-output"),
                                    ],
                                    className="proof-column",
                                ),
                            ],
                            className="proof-grid",
                        ),
                    ],
                    className="panel",
                ),
            ],
            className="page-shell",
        ),
    ]
)

page2_layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.P("NDSA · source model", className="eyebrow"),
                        html.H1("Knowledge base"),
                        html.P(title.values[0][0], className="lede"),
                    ]
                ),
                dcc.Link("Back to visualization", href="/", className="secondary-link"),
            ],
            className="app-header",
        ),
        html.Main(
            [
                html.Section(
                    [
                        dash_table.DataTable(
                            id="table",
                            columns=[{"name": i, "id": i} for i in df.columns],
                            data=df.to_dict("records"),
                            page_size=20,
                            sort_action="native",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
                                "fontSize": 13,
                                "padding": "10px",
                                "maxWidth": 320,
                            },
                            style_header={"fontWeight": 700, "backgroundColor": "#f2f4f7"},
                        ),
                    ],
                    className="panel",
                ),
                html.Section(
                    [
                        html.H2("Field guide"),
                        dcc.Markdown(
                            """
- **number** — source passage identifier. `T` = Trump, `B` = Biden, `C` = conclusion, `N` = norm.
- **origin** — original debate passage.
- **speaker** — participant associated with the passage.
- **type** — statement, conclusion, or strict/defeasible unexpressed premise.
- **proof** — shortened natural-language form used in explanations.
- **proposition** — symbolic representation used by the proof machinery.
- **group** — argument family used to bound the search space.
                            """
                        ),
                    ],
                    className="panel prose-panel",
                ),
            ],
            className="page-shell",
        ),
    ]
)


@app.callback(
    [
        dash.dependencies.Output("main-graph", "figure"),
        dash.dependencies.Output("extension", "data"),
        dash.dependencies.Output("main-graph", "clickData"),
    ],
    [dash.dependencies.Input("candidate-dropdown", "value")],
)
def main_work(claim):
    if not claim:
        raise dash.exceptions.PreventUpdate

    extension, separated_premises = load_argument_state(claim)
    payload = {
        "extension": _serialize_extension(extension),
        "premises": separated_premises,
    }
    return argument_graph(extension), payload, None


@app.callback(
    [
        dash.dependencies.Output("dialogical", "figure"),
        dash.dependencies.Output("premises-dropdown", "options"),
        dash.dependencies.Output("premises-dropdown", "value"),
        dash.dependencies.Output("argument-detail", "children"),
        dash.dependencies.Output("dialogical-status", "children"),
    ],
    [
        dash.dependencies.Input("extension", "data"),
        dash.dependencies.Input("main-graph", "clickData"),
    ],
)
def after_click(payload, argument):
    if not payload:
        raise dash.exceptions.PreventUpdate

    extension = _restore_extension(payload["extension"])
    arg_number = 0
    if argument and argument.get("points"):
        custom_data = argument["points"][0].get("customdata")
        if custom_data:
            arg_number = int(custom_data[0])

    if arg_number not in extension.arguments:
        arg_number = 0

    _, conclusion, _, claim_text = _argument_data(extension, arg_number)
    figure, statuses = dialogical_graph(extension, arg_number)
    options = build_premise_options(payload.get("premises", {}), conclusion, claim_text)
    status_children = [html.Span(status, className="tree-status-pill") for status in statuses]
    return figure, options, None, build_argument_detail(extension, arg_number), status_children


@app.callback(
    [
        dash.dependencies.Output("selected-premises", "children"),
        dash.dependencies.Output("claim", "children"),
        dash.dependencies.Output("NLP", "children"),
    ],
    [dash.dependencies.Input("premises-dropdown", "value")],
)
def after_choose_premises(raw_value):
    if not raw_value:
        return "", "", html.P("Select a premise set to generate the derivation.", className="muted")

    selected = json.loads(raw_value)
    premises = selected["premises"]
    conclusion = selected["conclusion"]

    with redirect_stdout(io.StringIO()):
        proof = NaturalDeduction(premises, conclusion).prove()

    nlp = natural_language_transform(proof)
    return selected["premises_text"], selected["claim_text"], dcc.Markdown(nlp)


@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")],
)
def display_page(pathname):
    return page2_layout if pathname == "/use-case" else page1_layout


app.layout = html.Div([dcc.Location(id="url", refresh=False), html.Div(id="page-content")])


if __name__ == "__main__":
    app.run_server(debug=False)
