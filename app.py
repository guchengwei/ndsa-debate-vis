import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html

import ast
import json
import re
import sys
import io
import pandas as pd

import plotly.graph_objects as go
import networkx as nx
import igraph

from argument_engine.argument import *
from argument_engine.natural_deduction import *

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, suppress_callback_exceptions=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width"}])
server = app.server

file_path = 'data/debate kb.csv'

title = pd.read_csv(file_path, nrows=1, header=None)

df = pd.read_csv(file_path, header=1)


def update_options():
    option_list = []

    for item in df.itertuples():

        if item.number.startswith('T'):
            an_option = {'label': 'From Trump: ' + item.proof, 'value': item.proposition}
        elif item.number.startswith('B'):
            an_option = {'label': 'From Biden: ' + item.proof, 'value': item.proposition}
        elif item.number.startswith('C'):
            an_option = {'label': 'In conclusion: ' + item.proof, 'value': item.proposition}
        elif item.number.startswith('N'):
            continue

        else:
            print('ERROR')
            raise Exception

        option_list.append(an_option)

    return option_list


# colors = {
#     "boxBackground": "#ffffff",
#     "graphBackground": "#D4D4D4",
#     "background": "#F5F5F5",
#     "text": "#000000"
# }

# layout = dict(
#     autosize=True,
#     automargin=True,
#     margin=dict(l=30, r=30, b=20, t=40),
#     hovermode="closest",
#     plot_bgcolor="#F9F9F9",
#     paper_bgcolor="#F9F9F9",
#     legend=dict(font=dict(size=10), orientation="h"),
#     title="Overview"
# )

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflow': 'auto',
        'paddingLeft': '10px',
        'fontFamily': '"Lucida Console", Courier, monospace'
    }
}

style = {
    'border': 'thin lightgrey solid',
    'overflow': 'auto',
    'paddingLeft': '10px',
    'fontFamily': '"Lucida Console", Courier, monospace',
    'whiteSpace': 'pre-wrap',

}

app.title = 'NDSA Visualization'

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

page1_layout = html.Div(
    [
        html.Div(id='extension', style={'display': 'none'}),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.H1("NDSA Debate Visualization"),
                    ],
                    className="one-half column",
                    id="title",
                ),

                html.Div(
                    [
                        html.H3("The second presidential debate"),
                        html.H5(title.values[0][0]),
                        dcc.Link('Go to knowledge-base', href='/use-case'),
                    ],
                    className="one-half column",
                    id="link",
                )
            ],
            id="header",
            className="row flex-display",
            style={"marginBottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Markdown('''
                        **Choose a claim** to draw the corresponding argument relation graph
                        '''),

                        dcc.Dropdown(
                            id="candidate-dropdown",
                            placeholder='Select a claim',
                            options=update_options(),
                            optionHeight=100,
                            multi=False,
                            # value=[],
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container twelve columns",
                    id="options",
                ),

            ],
            className="row flex-display",
        ),

        html.Div([

            dcc.Markdown(
                '''###### **Argument Relation Graph** displays the relation between arguments related to the chosen claim ''')

        ], className="pretty_container seven columns"
        ),

        html.Div(
            [
                html.Button('Redraw', id='redraw', n_clicks=0),
                dcc.Loading(
                    id="loading",
                    type="default",
                    fullscreen=True,
                    children=[html.Div(dcc.Graph(id="main-graph"))]
                ),
            ],

            className="pretty_container twelve columns",
        ),

        html.Div([

            dcc.Markdown('''
            ###### **Dialogical Explanation** is a simulation of a debate over the chosen claim &nbsp;&nbsp; >click an argument in the graph above to start<
                        ''')

        ], className="pretty_container nine columns"
        ),

        html.Div(
            [

                dcc.Loading(
                    id="loading2",
                    type="circle",
                    fullscreen=True,
                    children=[html.Div(dcc.Graph(id="dialogical"))]
                ),

            ],
            className="pretty_container twelve columns",
        ),

        html.Div(
            [
                html.Div(
                    [
                        dcc.Markdown('''
                        **Select a set of premises** to see a derivation inside of the chosen argument
                        '''),

                        dcc.Dropdown(
                            id="premises-dropdown",
                            placeholder='Hover to see detail',
                            multi=False,
                            # value=[],
                            className='dcc_control'
                        ),

                        html.Hr(),

                        html.P('Selected Premises'),

                        html.Pre(id='selected-premises', style=style),

                        html.Hr(),

                        html.P('Claim'),

                        html.Pre(id='claim', style=style)
                    ],
                    className="pretty_container six columns"
                ),

                html.Div(
                    [
                        html.Div([
                            dcc.Markdown('''
                            ###### **Natural Language Explanation** gives a proof about the chosen argument
                            ''')
                        ], className="pretty_container twelve columns"),

                        html.Div(id='NLP', className="pretty_container twelve columns")],

                    className="pretty_container six columns"
                )
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

app.clientside_callback(
    dash.dependencies.ClientsideFunction(namespace="clientside", function_name="resize"),
    dash.dependencies.Output("output-clientside", "children"),
    [dash.dependencies.Input("main-graph", "figure")],
)


@app.callback([dash.dependencies.Output('main-graph', 'figure'),
               dash.dependencies.Output('extension', 'children')
               ],
              [dash.dependencies.Input('candidate-dropdown', 'value'),
               dash.dependencies.Input('redraw', 'n_clicks')
               ])
def main_work(claim, n_clicks):
    if not claim:
        raise dash.exceptions.PreventUpdate

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'redraw' in changed_id:
        redraw = True
    else:
        redraw = False

    try:
        with open('data/cache_ext.txt') as cache_file:
            ext_dic = json.load(cache_file)

        raw_ext = ast.literal_eval(ext_dic[claim].replace('set()', '"empty_set"'))  # because ast cannot read set()

        for key in raw_ext:
            if isinstance(raw_ext[key], list):
                raw_ext[key] = [set() if item == 'empty_set' else item for item in raw_ext[key]]
            else:
                if raw_ext[key] == 'empty_set':
                    raw_ext[key] = set()

        extension = Extensions.__new__(Extensions)
        extension.__dict__.update(raw_ext)

        with open('data/cache_premises.txt') as cache_file:
            premises_dic = json.load(cache_file)

        separated_set_of_premises = premises_dic[claim]

    except:

        knowledge_base = copy.deepcopy(df)

        arguments, relation, separated_set_of_premises = FindArgument(knowledge_base).find_all(claim, combine=True)

        extension = Extensions(arguments, relation)

    dumped = json.dumps(str(extension.__dict__.copy()))

    figure = argument_graph(extension, separated_form=separated_set_of_premises, redraw=redraw)

    return figure, dumped


@app.callback([dash.dependencies.Output('dialogical', 'figure'),
               dash.dependencies.Output("premises-dropdown", "options")],
              [dash.dependencies.Input('extension', 'children'),
               dash.dependencies.Input('main-graph', 'clickData')])
def after_click(dumped_extension, argument):
    # print(argument)

    if dumped_extension is None or argument is None:
        raise dash.exceptions.PreventUpdate

    else:
        dumped = ast.literal_eval(json.loads(dumped_extension).replace('set()', '"empty_set"'))

    for key in dumped:
        if isinstance(dumped[key], list):
            dumped[key] = [set() if item == 'empty_set' else item for item in dumped[key]]
        else:
            if dumped[key] == 'empty_set':
                dumped[key] = set()

    extension = Extensions.__new__(Extensions)
    extension.__dict__.update(dumped)

    try:
        union_form = argument['points'][0]['hovertext']
        detail_info = argument['points'][0]['hovertemplate']
    except:
        raise dash.exceptions.PreventUpdate

    arg_number = int(re.findall(r'A(\d+)', union_form)[0])

    # arg = extension.original_arg[arg_number]

    figure = dialogical_graph(extension, arg_number)

    raw_premise = re.findall(r'\{(.+?)\}', union_form)

    conclusion = re.findall(r'\|- (.+)', union_form)[0]

    claim = re.findall(r'claims that<br><b>(.*?\.)<\/b>', detail_info)[0]

    # premises = re.findall(r'<br><b>([^<>]*?<\/b>[^<>]*?\.)<br>', detail_info)

    options = []
    set_number = 1
    for item in raw_premise:
        set_length = len(item.split(', '))

        premise_text = generate_support_claim_text(df, item.split(', '))
        premise_text = premise_text.replace('<b>', '')
        premise_text = premise_text.replace('</b>', '')
        premise_text = premise_text.replace('<br>', '\n')
        premise_text = premise_text  # remove \n at the end of string

        set_info = 'Set number ' + str(set_number) + ', containing ' + str(set_length)
        if set_length > 1:
            set_info += ' premises'
        else:
            set_info += ' premise'

        options.append({'label': set_info, 'title': premise_text,
                        'value': '(' + item + ' AND ' + conclusion + ')'
                                                                     '[' + premise_text + ' BREAK-LINE ' + claim + ']'})

        set_number += 1

    return figure, options


@app.callback([
    dash.dependencies.Output('selected-premises', 'children'),
    dash.dependencies.Output('claim', 'children'),
    dash.dependencies.Output('NLP', 'children')],
    [dash.dependencies.Input('premises-dropdown', 'value')])
def after_choose_premises(premises_and_conclusion):
    if not premises_and_conclusion:
        raise dash.exceptions.PreventUpdate

    premises, conclusion = re.findall(r'\((.+) AND (.+)\)', str(premises_and_conclusion))[0]

    premises_text, conclusion_text = re.findall(r'\[([\w\W]*) BREAK-LINE ([\w\W]*)\]', str(premises_and_conclusion))[0]

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    ndp = NaturalDeduction(premises.split(', '), conclusion).prove()

    sys.stdout = old_stdout

    nlp = natural_language_transform(ndp)

    nlp_output = dcc.Markdown([nlp])
    # nlp_output = html.Pre([nlp], style=style)

    return [premises_text], [conclusion_text], nlp_output


def deal_with_not(clause):
    number_of_not = 0
    add_not = False
    while True:

        if clause.startswith('~('):
            n_clause = clause[2:-1]

        elif clause.startswith('~'):
            n_clause = clause[1:]

        else:
            if len(clause) == 1:
                n_clause = '~' + clause
            else:
                n_clause = '~(' + clause + ')'

            add_not = True

        number_of_not += 1

        match = df.loc[df['proposition'] == n_clause]

        if not match.empty:
            break
        elif add_not:
            raise Exception
        else:
            clause = n_clause

    return match, number_of_not


def natural_language_transform(proof):
    nlp = ''

    proof_list = proof.split('\n')[:-1]

    prop_list = ['']
    index = 0

    while index < len(proof_list):
        prefix = re.search(r'[0-9]+\.[\s\|]+', proof_list[index])

        raw_prop = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+', proof_list[index][prefix.end():])
        prop = raw_prop.group().strip(' ')
        match = df.loc[df['proposition'] == prop]
        if match.empty:
            raw_clause, number_of_not = deal_with_not(prop)

            clause = '_it is not the case that_ '

            while number_of_not > 1:
                clause += '_it is not the case that_ '
                number_of_not -= 1

            clause += [item.proof for item in raw_clause.itertuples()][0]

        else:
            clause = [item.proof for item in match.itertuples()][0]

        prop_list.append(clause)

        if prefix.group().count('|') == 1:

            if 'Premise' not in proof_list[index]:
                number = re.findall(r'[0-9]+', proof_list[index][prefix.end():])
                if len(number) == 1:
                    nlp += '__We have__ ' + clause + ', __given that__ ' + prop_list[int(number[0])] + '.\n\n'
                else:
                    nlp += '__We have__ ' + clause + ', __given that__ '
                    nlp += ' __and__ '.join([prop_list[int(item)] for item in number])
                    nlp += '.\n\n'

        else:
            # record assumed prop (unfinished)
            if 'RAA Assume' in proof_list[index]:

                while re.search(r'[0-9]+\.[\s\|]+', proof_list[index]).group().count('|') != 1:
                    index += 1
                    prop_list.append('')

                if 'Therefore' in proof_list[index]:
                    therefore = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+',
                                          proof_list[index][re.search(r'[0-9]+\.[\s\|]+', proof_list[index]).end():]) \
                        .group().strip(' ')

                    therefore_match = df.loc[df['proposition'] == therefore]

                    if therefore_match.empty:
                        raw_therefore, number_of_not = deal_with_not(therefore)

                        str_therefore = '_it is not the case that_ '

                        while number_of_not > 1:
                            str_therefore += '_it is not the case that_ '
                            number_of_not -= 1

                        str_therefore += [item.proof for item in raw_therefore.itertuples()][0]

                    else:
                        str_therefore = [item.proof for item in therefore_match.itertuples()][0]
                else:
                    raise Exception

                prop_list.append(str_therefore)

                nlp += '__If we assume that__ ' + clause + ', __we will meet a contradiction. Therefore, we have__ ' + \
                       str_therefore + '.\n\n'

            elif 'IfI Assume' in proof_list[index]:
                while re.search(r'[0-9]+\.[\s\|]+', proof_list[index]).group().count('|') != 1:
                    index += 1
                    prop_list.append('')

                if 'Therefore' in proof_list[index]:
                    n_prefix = re.search(r'[0-9]+\.[\s\|]+', proof_list[index])

                    therefore = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+',
                                          proof_list[index][n_prefix.end():]).group().strip(' ')

                    therefore_match = df.loc[df['proposition'] == therefore]

                    if therefore_match.empty:
                        raw_therefore, number_of_not = deal_with_not(therefore)

                        str_therefore = '_it is not the case that_ '

                        while number_of_not > 1:
                            str_therefore += '_it is not the case that_ '
                            number_of_not -= 1

                        str_therefore += [item.proof for item in raw_therefore.itertuples()][0]

                    else:
                        str_therefore = [item.proof for item in therefore_match.itertuples()][0]

                    conclusion_number = int(re.findall(r'[0-9]+', proof_list[index][n_prefix.end():])[1])

                    conclusion_if = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+',
                                              proof_list[conclusion_number - 1]
                                              [re.search(r'[0-9]+\.[\s\|]+',
                                                         proof_list[conclusion_number - 1]).end():]).group().strip(' ')

                    conclusion_match = df.loc[df['proposition'] == conclusion_if]

                    if conclusion_match.empty:
                        raw_conclusion, number_of_not = deal_with_not(conclusion_if)

                        str_conclusion = '_it is not the case that_ '

                        while number_of_not > 1:
                            str_conclusion += '_it is not the case that_ '
                            number_of_not -= 1

                        str_conclusion += [item.proof for item in raw_conclusion.itertuples()][0]

                    else:
                        str_conclusion = [item.proof for item in conclusion_match.itertuples()][0]

                else:
                    raise Exception

                nlp += '__If we assume that__ ' + clause + ', __we will get__ ' + str_conclusion + \
                       '. __Therefore, we have__ ' + str_therefore + '.\n\n'

            elif 'Or Assume' in proof_list[index]:
                str_assume2 = ''
                while re.search(r'[0-9]+\.[\s\|]+', proof_list[index]).group().count('|') != 1:
                    index += 1
                    if 'Or Assume' in proof_list[index]:
                        assume2 = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+',
                                            proof_list[index][re.search(r'[0-9]+\.[\s\|]+',
                                                                        proof_list[index]).end():]).group().strip(' ')

                        assume2_match = df.loc[df['proposition'] == assume2]

                        if assume2_match.empty:

                            raw_assume2, number_of_not = deal_with_not(assume2)

                            str_assume2 = '_it is not the case that_ '

                            while number_of_not > 1:
                                str_assume2 += '_it is not the case that_ '
                                number_of_not -= 1

                            str_assume2 += [item.proof for item in raw_assume2.itertuples()][0]

                        else:
                            str_assume2 = [item.proof for item in assume2_match.itertuples()][0]

                        prop_list.append(str_assume2)

                    else:
                        prop_list.append('')

                if 'Therefore' in proof_list[index]:
                    therefore = re.search(r'([^\w]|\b)([a-z\|\&\>\~\(\)])+',
                                          proof_list[index][re.search(r'[0-9]+\.[\s\|]+', proof_list[index]).end():]) \
                        .group().strip(' ')

                    therefore_match = df.loc[df['proposition'] == therefore]

                    if therefore_match.empty:
                        raw_therefore, number_of_not = deal_with_not(therefore)

                        str_therefore = '_it is not the case that_ '

                        while number_of_not > 1:
                            str_therefore += '_it is not the case that_ '
                            number_of_not -= 1

                        str_therefore += [item.proof for item in raw_therefore.itertuples()][0]

                    else:
                        str_therefore = [item.proof for item in therefore_match.itertuples()][0]

                else:
                    raise Exception

                prop_list.append(str_therefore)

                nlp += '__We will get__ ' + str_therefore + ' __by assume either__ ' + clause + ' __or__ ' + \
                       str_assume2 + '. __Therefore, we have__ ' + str_therefore + '.\n\n'

            else:
                raise Exception

        index += 1

    if nlp == '':
        nlp = '__The claim only supported by itself.__'

    return nlp


def dialogical_graph(extension, arg_number):
    edges, vertices, node_dict, arg_dict, root_dict = extension.dialogical_explanations(arg_number)
    g = igraph.Graph()
    g.add_vertices(vertices)
    g.add_edges(edges)
    graph_layout = g.layout('rt', root=[key for key in root_dict])
    position = {k: graph_layout[k] for k in range(vertices)}
    Xn = [position[k][0] for k in range(vertices)]
    Yn = [-position[k][1] for k in range(vertices)]
    Xe = []
    Ye = []
    for E in edges:
        Xe += [position[E[0]][0], position[E[1]][0], None]
        Ye += [-position[E[0]][1], -position[E[1]][1], None]

    node_labels = []
    hover_labels = []
    p_o_color = []
    text_length = 40 if vertices < 20 else 25

    for k in range(vertices):

        if not arg_dict.get(k):
            hover_labels.append('We found that in the current situation,<br>' + node_dict.get(k))
            node_labels.append(node_dict.get(k) if len(node_dict.get(k)) < text_length
                               else node_dict.get(k)[:text_length - 3] + '...')
        else:

            raw_premise, conclusion = re.findall(r'\{(.+)\}\|-(.+)', arg_dict.get(k))[0]
            premise = raw_premise.split(', ')

            support_text, claim_text = generate_support_claim_text(df, premise, conclusion)

            if len(claim_text) > text_length:
                node_labels.append(node_dict.get(k)[:1] + ':' + claim_text[:text_length] + '...')
            else:
                node_labels.append(node_dict.get(k)[:1] + ':' + claim_text)

            if claim_text.startswith('<b>'):
                claim_text = claim_text.replace('<b>not that</b>', 'not that')

            if k in root_dict:
                node_message = 'Proponent first claims that '
            elif node_dict.get(k).startswith('P'):
                node_message = 'Proponent defends itself against opponent claiming that '
            else:
                node_message = 'Opponent counterattacks proponent claiming that '

            single_hover_label = f"{node_message}<br><b>{claim_text}</b>.<br><br><br>" + \
                                 f"which is supported by:<br><br>{support_text}"

            if len(single_hover_label) > 1000:
                single_hover_label = single_hover_label[:1000] + '...'

            hover_labels.append(single_hover_label)

        if node_dict.get(k).startswith('P'):
            p_o_color.append('#6722B0')
        elif node_dict.get(k).startswith('O'):
            p_o_color.append('DarkOrange')
        else:
            p_o_color.append('#046E94')

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=Xe,
                             y=Ye,
                             mode='lines',
                             line=dict(color='rgb(210,210,210)', width=1),
                             hoverinfo='none'
                             ))
    fig.add_trace(go.Scatter(x=Xn,
                             y=Yn,
                             mode='text',
                             textfont=dict(size=12, color=p_o_color),
                             text=node_labels,
                             hovertext=hover_labels,
                             hoverlabel=dict(bgcolor=p_o_color),
                             hoverinfo='text',
                             ))

    fig.update_layout(annotations=[dict(showarrow=True, arrowhead=2, arrowcolor='#DC2808',
                                        arrowsize=2, arrowwidth=1, opacity=0.5,
                                        ax=(position[E[1]][0] * 9 +
                                            position[E[0]][0]) / 10,
                                        ay=(-position[E[1]][1] * 9 +
                                            -position[E[0]][1]) / 10,
                                        axref='x', ayref='y',
                                        x=(position[E[0]][0] * 9 +
                                           position[E[1]][0]) / 10,
                                        y=(-position[E[0]][1] * 9 +
                                           -position[E[1]][1]) / 10,
                                        xref='x', yref='y') for E in edges])

    # axis = dict(showline=True,  # hide axis line, grid, ticklabels and  title
    #             zeroline=True,
    #             showgrid=True,
    #             showticklabels=True,
    #             range=[min(Xn) * 1.2, max(Xn) * 1.2]
    #             )

    fig.update_layout(
        title='hover to see detail',
        autosize=True,
        # legend=dict(font=dict(size=10), orientation="h"),
        showlegend=False,
        xaxis=dict(showline=True,
                   zeroline=True,
                   showgrid=True,
                   showticklabels=False,
                   range=[min(Xn) * 1.2, max(Xn) * 1.2]
                   ),
        yaxis=dict(showline=True,
                   zeroline=True,
                   showgrid=True,
                   showticklabels=False
                   ),
        margin=dict(l=20, r=20, b=20, t=40),
        hovermode='closest',
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",

    )

    for key in root_dict:
        tree_text = root_dict[key]

        if tree_text == 'not a dispute tree':
            tree_text = f'Clicked argument A{arg_number} is <b>not accepted</b> because<br>' \
                        f'proponent cannot defend itself against opponent.'
        elif tree_text == 'not admissible':
            tree_text = f'Clicked argument A{arg_number} is <b>not accepted</b> because<br> ' \
                        f'an argument is used by both proponent and opponent.'
        elif tree_text == 'admissible':
            tree_text = f'Clicked argument A{arg_number} is <b>admissible</b> because<br>' \
                        f'proponent can defend itself against opponent.'
        elif tree_text == 'grounded':
            tree_text = f'Clicked argument A{arg_number} is <b>grounded</b> because<br>' \
                        f'the debate won\'t last forever.'
        elif tree_text == 'ideal':
            tree_text = f'Clicked argument A{arg_number} is <b>ideal</b> because<br>' \
                        f'either no opponent can counterattack proponent or <br>' \
                        f'no argument used by opponent is admissible.'
        elif tree_text == 'grounded,ideal':
            tree_text = f'Clicked argument A{arg_number} is <b>grounded</b> and <b>ideal</b> because<br>' \
                        f'(1) the debate won\'t last forever;<br>' \
                        f'(2) either no opponent can counterattack proponent or<br>' \
                        f'no argument used by opponent is admissible.'
        else:
            tree_text = 'ERROR'

        fig.add_annotation(x=position[key][0],
                           y=-position[key][1],
                           text=tree_text,
                           showarrow=False,
                           yshift=60,
                           font=dict(color='rgb(0,0,0)', size=20))

    # fig.show()
    return fig


def argument_graph(extension, separated_form=None, redraw=False):
    G = nx.DiGraph()
    for index in extension.arguments:
        raw_premise, conclusion = re.findall(r'\{(.+)\}\|-(.+)', extension.original_arg[index])[0]
        premises = raw_premise.split(', ')

        G.add_node(index, supports=premises, claim=conclusion)
        for another_index in extension.attackee[index]:
            G.add_edge(index, another_index)

    if redraw:
        pos = nx.spring_layout(G, k=1)
    else:
        pos = nx.kamada_kawai_layout(G)

    max_x = max(pos[key][0] for key in pos)
    min_x = min(pos[key][0] for key in pos)
    max_y = max(pos[key][1] for key in pos)
    min_y = min(pos[key][1] for key in pos)

    for node in G.nodes:
        G.nodes[node]['pos'] = list(pos[node])

    figure = go.Figure()

    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']

        figure.add_trace(go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]), mode='lines', showlegend=False,
                                    line=dict(width=1.5, color='#888'), hoverinfo='none', opacity=0.2))

        hovertext = "A" + str(edge[0]) + " attacks " + "A" + str(edge[1])
        figure.add_trace(go.Scatter(x=tuple([(x0 + x1 * 3) / 4]), y=tuple([(y0 + y1 * 3) / 4]),
                                    hovertext=hovertext, mode='text', showlegend=False,
                                    hoverlabel=dict(bgcolor='white', font_size=16),
                                    hoverinfo='text', marker=dict(size=20), opacity=0))

    figure.update_layout(
        title={
            'text': "Hover to see detail",
            'y': 1.0,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        autosize=True,
        hovermode='closest',
        margin=dict(b=20, l=20, r=20, t=60),
        xaxis=dict(showgrid=True, zeroline=True, showticklabels=False,
                   range=[min_x * 1.3, max_x * 1.3]),
        yaxis=dict(showgrid=True, zeroline=True, showticklabels=False,
                   range=[min_y * 1.3, max_y * 1.3]),
        height=600,
        clickmode='event',
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        annotations=[dict(showarrow=True, arrowhead=2, arrowcolor='#6495ED',
                          arrowsize=2, arrowwidth=1, opacity=0.5,
                          ax=(G.nodes[edge[0]]['pos'][0] * 3 +
                              G.nodes[edge[1]]['pos'][0]) / 4,
                          ay=(G.nodes[edge[0]]['pos'][1] * 3 +
                              G.nodes[edge[1]]['pos'][1]) / 4,
                          axref='x', ayref='y',
                          x=(G.nodes[edge[1]]['pos'][0] * 3 +
                             G.nodes[edge[0]]['pos'][0]) / 4,
                          y=(G.nodes[edge[1]]['pos'][1] * 3 +
                             G.nodes[edge[0]]['pos'][1]) / 4,
                          xref='x', yref='y') for edge in G.edges])

    for node in G.nodes:
        x, y = G.nodes[node]['pos']

        hovertext = 'A' + str(node) + '： ' + separated_form[str(G.nodes[node]['claim'])] + \
                    ' |- ' + str(G.nodes[node]['claim'])

        support_text, claim_text = generate_support_claim_text(df, G.nodes[node]['supports'], G.nodes[node]['claim'])

        if len(claim_text) >= 40:  # max length of a annotate text is 40

            text = claim_text[:38] + '...'

        else:
            text = claim_text

        if text.startswith('<b>'):
            text = text[:3] + text[3].capitalize() + text[4:]
        else:
            text = text[0].capitalize() + text[1:]

        if claim_text.startswith('<b>'):
            claim_text = claim_text.replace('<b>not that</b>', 'not that')

        hovertemplate = f"Argument <b>A{str(node)}</b> claims that<br><b>{claim_text}.</b><br><br><br>" + \
                        f"which is supported by following (statement or assumption):<br><br>{support_text}"

        size = int(17 + 5 * len(extension.attackee[node]) / len(extension.arguments))  # follow Out-Degrees

        if str(node) == '0':
            color = '#FBB234'
        else:
            color = '#78CD3F'

        figure.add_trace(
            go.Scatter(x=tuple([x]), y=tuple([y]), text=tuple([text]), hovertext=tuple([hovertext]),
                       hovertemplate=tuple([hovertemplate]),
                       hoverinfo='text', mode='text', textposition='middle center',
                       hoverlabel=dict(bgcolor=color, font_size=16),
                       name='A' + str(node),
                       showlegend=False,
                       textfont=dict(size=size, color=color)
                       ))

    return figure


def generate_support_claim_text(dataframe, supports_list, claim_str=None):
    support_text = ''

    for prop in supports_list:
        support = dataframe.loc[dataframe['proposition'] == str(prop)]

        single_text = [item.proof for item in support.itertuples()][0]

        if [item.type for item in support.itertuples()][0].startswith('statement'):
            if [item.speaker for item in support.itertuples()][0].startswith('D'):
                support_type = '<b>Trump\'s statement</b>'
            else:
                support_type = '<b>Biden\'s statement</b>'
        else:
            support_type = '<b>assumption</b>'

        support_text += support_type + ': ' + single_text[0].capitalize() + single_text[1:] + '.<br><br>'

    if claim_str:
        claim = dataframe.loc[dataframe['proposition'] == str(claim_str)]

        if claim.empty:
            claim, number_of_not = deal_with_not(str(claim_str))

            claim_text = '<b>not that</b> '

            while number_of_not > 1:
                claim_text += '<b>not that</b> '
                number_of_not -= 1

            claim_text += [item.proof for item in claim.itertuples()][0]

        else:
            claim_text = [item.proof for item in claim.itertuples()][0]

        return support_text.strip('<br><br>'), claim_text

    else:
        return support_text.strip('<br><br>')


def wrap_text(original_text, character_per_line, how_many_line):
    output_text = ''
    line_number = 1
    index = 0

    while line_number <= how_many_line:

        if len(original_text) >= line_number * character_per_line + index:

            output_text += original_text[((line_number - 1) * character_per_line + index):
                                         (line_number * character_per_line + index)]

            while original_text[line_number * character_per_line + index] != ' ':
                output_text += original_text[line_number * character_per_line + index]
                index += 1
                if len(original_text) <= how_many_line * character_per_line + index:
                    break

            output_text += '<br>'
        else:
            output_text += original_text[((line_number - 1) * character_per_line + index):]

        line_number += 1

    if len(original_text) >= how_many_line * character_per_line + index:
        output_text += '...'

    return output_text


page2_layout = html.Div([

    dcc.Link('Go back to visualization', href='/'),
    html.Br(),
    html.H5(title.values[0][0]),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
    ),
    html.H6('Description'),

    dcc.Markdown(
        '''
    * number: The serial number of each passage.\

        * C stands for conclusion.
        * N stands for norm.
        * T stands for Trump's speech.
        * B stands for Biden's speech.\
              
    * origin: the origin speech passage extracted from the debate transcript.\

    * speaker: who the passage related to.\

    * type: indicates the type of each passage.\
        
        * statement: a passage extracted from the original speech.\
        
        * conclusion: statement that can be treated as a conclusion of the whole speech.\
        
            * Conclusion that is not in the original speech but given implicitly has (hidden) mark.\
                         
        * norm()[]: also called unexpressed premises, added accordingly in order to 
                       transform __enthymematic__ proof into __syllogistic__ proof.\
                       
            * Within the () can be strict or defeasible. Strict means that this norm are treated as truth, 
                   therefore cannot be attacked. Defeasible means this norm can be attacked.\
                   
            * Within the [] is the statement the norm corresponding to.\
              
    * proof: a summary of the original speech passage that shown in the detail and proof.\

    * proposition: act as a code of the passage to go through the proof machinery.\

    * group: indicates which group the passage belongs to.\
    
        * Each group is named after the proposition of one of the conclusions.\
                
        * In this knowledge base, conclusion = {c, p, a, b, ~b, ~c} and group = {c, p, a, b}.\
                
        * Note that b and ~b as well as c and ~c are in the same group for they attack each other.\
    '''
    ),

])


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/use-case':
        return page2_layout
    else:
        return page1_layout


if __name__ == "__main__":
    app.run_server(debug=True)
    # app.run_server(debug=False)
