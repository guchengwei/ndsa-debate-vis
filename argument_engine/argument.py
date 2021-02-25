import copy
import pandas
import random
import re

from argument_engine.tableaux import *
from itertools import chain, combinations, product


class Argument:
    def __init__(self, supports, claim, group=None):
        self.supports = supports
        self.claim = claim
        self.group = group
        self.attack = []

    def __str__(self):
        """
        print out arguments as {a, a>b} |- b form
        """
        supports = ", ".join(map(str, self.supports))
        return "{" + supports + "}" + "|-" + str(self.claim)


def power_set(iterable, combination_number_min, combination_number_max):
    """
    power_set([1,2,3]) --> [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]
    """
    tuple_form = chain.from_iterable(combinations(iterable, r) for r in
                                     range(combination_number_min, combination_number_max + 1))
    list_form = [list(item) for item in tuple_form]
    return list_form


class FindArgument:
    def __init__(self, knowledge_base):
        self.df = knowledge_base
        self.argument_list = []
        self.kb = []

    def find_all(self, claim, combine=False):

        corresponding_row = self.df.loc[self.df['proposition'] == claim]

        group = [item for item in corresponding_row['group']][0]

        if len(group) > 1:  # deal with claim belongs to two or more groups
            group = list(group)[random.randint(0, len(group) - 1)]

        for prop in self.df.loc[(self.df['group'].str.contains(group))
                                & (~self.df['type'].str.contains('conclusion'))]['proposition']:
            self.kb.append(SymbolToFunction(prop).transform())

        self.find_relative(claim)

        if combine:
            separated_set_of_premises = self.slim()

            attack_map = self.attack_relation()

            return self.argument_list, attack_map, separated_set_of_premises

        else:
            attack_map = self.attack_relation()

            return self.argument_list, attack_map

    def slim(self):
        new_arg_list = []

        arg_with_same_claim = []

        current_claim = str(self.argument_list[0].claim)

        for arg in self.argument_list:
            if str(arg.claim) == current_claim:
                arg_with_same_claim.append(arg)
            else:
                new_arg_list.append(arg_with_same_claim)

                arg_with_same_claim = []
                current_claim = str(arg.claim)
                arg_with_same_claim.append(arg)

        new_arg_list.append(arg_with_same_claim)

        self.argument_list = []
        separated_set_of_premises = dict()

        for a_set_of_args in new_arg_list:
            support = set()
            a_set_of_premises = []

            for arg in a_set_of_args:
                support.update(arg.supports)
                a_set_of_premises.append("{" + ", ".join(map(str, arg.supports)) + "}" )

            claim = a_set_of_args[0].claim
            self.argument_list.append(Argument(support, claim))
            separated_set_of_premises[str(claim)] = 'U'.join(a_set_of_premises)

        return separated_set_of_premises

    def find_relative(self, claim):
        if not isinstance(claim, Formula):
            claim = SymbolToFunction(claim).transform()

        defeasible_norm = self.df.loc[self.df['type'].str.contains('defeasible')]
        strict_norm = self.df.loc[self.df['type'].str.contains('strict')]

        strict_norm_list = [item for item in strict_norm['proposition']]
        strict_prop_list = [re.findall(f'\[(.*?)\]', item)[0] for item in defeasible_norm.type]
        cannot_be_attacked_set = set(strict_norm_list + strict_prop_list)

        if str(claim) in cannot_be_attacked_set:
            claim_list = [claim]
        else:
            claim_list = [claim, Not(claim) if not isinstance(claim, Not) else claim.args[0]]

        old_length = 0

        while True:
            new_length = len(claim_list)
            for index in range(old_length, new_length):
                n_argument_list = self.find_smallest_set(claim_list[index])
                if n_argument_list:
                    self.argument_list.extend(n_argument_list)

                    for arg in n_argument_list:
                        for support in arg.supports:

                            if str(support) not in cannot_be_attacked_set:  # Norm can not be attacked xx
                                n_support = Not(support) if not isinstance(support, Not) else support.args[0]
                                if not duplicates(n_support, claim_list):
                                    claim_list.append(n_support)

            if new_length == len(claim_list):
                break
            else:
                old_length = new_length

    def find_smallest_set(self, conclusion):
        power_set_kb = power_set(self.kb, 1, len(self.kb))  # questionable!!----update:
        argument_list = []
        a_kb = power_set_kb
        n_kb = []
        while True:
            for index in range(0, len(a_kb)):
                if Tableaux(copy.deepcopy(conclusion), premise_in_a_list=copy.deepcopy(a_kb[index])).prove(
                        consistency_test=True):
                    argument_list.append(Argument(a_kb[index], conclusion))
                    for n_index in range(index, len(a_kb)):
                        if not set(a_kb[index]).issubset(set(a_kb[n_index])):
                            n_kb.append(a_kb[n_index])

                    break
            if n_kb:
                a_kb = n_kb
                n_kb = []
            else:
                return argument_list

    def attack_relation(self):
        attack_map = []
        for arg_index in range(0, len(self.argument_list)):
            for another_arg_index in range(0, len(self.argument_list)):
                if another_arg_index == arg_index:
                    continue
                else:
                    for support in self.argument_list[another_arg_index].supports:
                        if TableauxProve([And(copy.deepcopy(self.argument_list[arg_index].claim),
                                              copy.deepcopy(support))], init='consistency').search():
                            self.argument_list[arg_index].attack.append(another_arg_index)
                            attack_map.append((arg_index, another_arg_index))
                            break

        return attack_map


class Extensions:
    def __init__(self, argument_list, attack_map):
        self.original_arg = [str(arg) for arg in argument_list]
        self.arguments = [i for i in range(len(argument_list))]
        self.relation = attack_map
        self.attacker = [{relation[0] for relation in self.relation if relation[1] == arg} for arg in self.arguments]
        self.attackee = [{relation[1] for relation in self.relation if relation[0] == arg} for arg in self.arguments]

        self.conflict_free = None
        self.admissible = None
        self.complete = None
        self.grounded = None
        self.preferred = None
        self.ideal = None

        self.admissible_extension()
        self.grounded_extension()
        self.ideal_extension()

    def conflict_free_extension(self):
        candidate = [set(item) for item in power_set(self.arguments, 1, len(self.arguments))]  # questionable
        attacks = [set(item) for item in self.relation]
        for attack in attacks:
            candidate = [item for item in candidate if not attack.issubset(item)]

        candidate.insert(0, set())
        self.conflict_free = candidate
        return candidate

    def admissible_extension(self):
        if not self.conflict_free:
            self.conflict_free_extension()

        candidate = []
        for arg_set in self.conflict_free:
            attackers = set()
            for arg in arg_set:
                attackers.update(self.attacker[arg])

            if not attackers or all(arg_set.intersection(self.attacker[attacker_of_attackers])
                                    for attacker_of_attackers in attackers):
                candidate.append(arg_set)

        self.admissible = candidate
        return candidate

    def complete_extension(self):
        if not self.admissible:
            self.admissible_extension()

        self.complete = []

        for a_set in self.admissible:
            attackee_set = set()
            for item in a_set:
                attackee_set.update(self.attackee[item])

            not_complete = False
            for arg in self.arguments:
                if arg not in a_set and self.attacker[arg].issubset(attackee_set):
                    not_complete = True
                    break

            if not not_complete:
                self.complete.append(a_set)

        return self.complete

    def grounded_extension(self):
        if not self.complete:
            self.complete_extension()

        candidate = copy.deepcopy(self.complete[0])
        index = 1
        while index < len(self.complete):
            candidate &= self.complete[index]
            index += 1

        self.grounded = candidate
        return candidate

    def preferred_extension(self):
        if not self.complete:
            self.complete_extension()

        candidate = [self.complete[-1]]
        index = len(self.complete) - 2
        while index >= 0:
            if any(self.complete[index].issubset(arg_set) for arg_set in candidate):
                index -= 1
                continue
            candidate.append(self.complete[index])
            index -= 1

        candidate.reverse()
        self.preferred = candidate
        return candidate

    def ideal_extension(self):
        if not self.preferred:
            self.preferred_extension()

        candidate = copy.deepcopy(self.preferred[0])
        index = 1
        while index < len(self.preferred):
            candidate &= self.preferred[index]
            index += 1

        if candidate not in self.complete:
            index = len(self.complete) - 1
            changed = False
            while index >= 0:
                if self.complete[index].issubset(candidate):
                    candidate = self.complete[index]
                    changed = True
                    break

                index -= 1

            if not changed:
                candidate = set()

        self.ideal = candidate

        return candidate

    def dialogical_explanations(self, arg_number):
        root = arg_number

        admissible = any(root in a_set for a_set in self.admissible)
        grounded = root in self.grounded
        ideal = root in self.ideal

        tree_list = self.dispute_tree(root, [admissible, grounded, ideal])
        return self.merge_trees(tree_list)

    def tree_type(self, tree):
        end_message = self.end_message(tree.root)
        if end_message.find('proponent cannot defend itself.') != -1:
            tree.type = 'not a dispute tree'
        elif end_message.find('an argument is used by both proponent and opponent.') != -1:
            tree.type = 'not admissible'
        else:
            if end_message.find('proponent can use an argument more than once,'
                                '<br> resulting in a never ending debate.') == -1:
                tree.type = 'grounded'
            o_set = copy.deepcopy(tree.o_set)
            if any(o_set.intersection(adm_set) for adm_set in self.admissible):
                if not tree.type:
                    tree.type = 'admissible'
            else:
                if not tree.type:
                    tree.type = 'ideal'
                else:
                    tree.type += ',ideal'

        return tree

    def end_message(self, node):
        end_message = ''
        if not node.o:
            end_message += node.end + ' '

        for o in node.o:
            new_node = node.children.get(o)
            if new_node.o:
                n_end_message = self.end_message(new_node)
                end_message += n_end_message
            else:
                end_message += new_node.end + ' '

        return end_message

    def dispute_tree(self, root, goal_list):

        result = []
        not_admissible = False if goal_list[0] else [True, True]

        root_tree = DisputeTree(root, self.attacker[root])

        tree_list = [root_tree]
        while True:
            n_tree_list = []
            for tree in tree_list:
                all_p_list = []
                for node in tree.layer[tree.current_layer]:
                    if not node.end:
                        if not node.o:
                            node.end = 'opponent cannot counterattack.'
                        for o in node.o:
                            p_of_o = list(self.attacker[o])
                            if not p_of_o:
                                node.end = 'proponent cannot defend itself.'
                            all_p_list.append(p_of_o)

                if [] in all_p_list or not all_p_list:
                    tree = self.tree_type(tree)

                    if not_admissible:
                        if tree.type == 'not a dispute tree' and not_admissible[0]:
                            result.append(tree)
                            not_admissible[0] = False
                            continue
                        elif tree.type == 'not admissible' and not_admissible[1]:
                            result.append(tree)
                            not_admissible[1] = False
                            continue
                        if not any(not_admissible[key] for key in not_admissible):
                            break
                    else:
                        if tree.type == 'admissible' and goal_list[0]:
                            result.append(tree)
                            goal_list[0] = False
                            continue
                        elif tree.type.startswith('grounded') and goal_list[1]:
                            result.append(tree)
                            goal_list[1] = False
                            continue
                        elif tree.type.endswith('ideal') and goal_list[2]:
                            result.append(tree)
                            goal_list[2] = False
                            continue

                        if not any(i for i in goal_list):
                            break
                    continue

                p_combination = list(product(*all_p_list))

                for combination in p_combination:
                    new_tree = copy.deepcopy(tree)
                    index = 0
                    new_layer = []
                    for node in new_tree.layer[new_tree.current_layer]:
                        if not node.end:
                            for o in node.o:
                                oppo_set = None
                                end = False
                                if combination[index] in new_tree.p_set:
                                    end = 'proponent can use an argument more than once,' \
                                          '<br> resulting in a never ending debate.'
                                elif combination[index] in new_tree.o_set:
                                    end = 'an argument is used by both proponent and opponent,' \
                                          '<br> resulting in self-attack.'
                                    if not_admissible:
                                        if not not_admissible[1]:
                                            new_tree = None
                                            break
                                else:
                                    oppo_set = self.attacker[combination[index]]
                                    new_tree.o_set = new_tree.o_set | oppo_set
                                    if not oppo_set:
                                        end = 'opponent cannot counterattack.'

                                new_tree.p_set.add(combination[index])
                                new_node = Node(combination[index], oppo_set, o, end)
                                node.children[o] = new_node
                                new_layer.append(new_node)
                                index += 1

                        if new_tree is None:
                            break

                    if new_tree is None:
                        continue
                    new_tree.layer.append(new_layer)
                    new_tree.current_layer += 1
                    n_tree_list.append(new_tree)

            if n_tree_list:
                tree_list = n_tree_list
            else:
                break

        return result

    def merge_trees(self, tree_list):
        shift = 0
        edge_list = []
        node_dict = dict()
        arg_dict = dict()
        root_list = dict()
        for tree in tree_list:
            edge = []
            edges, vertices, n_dict, a_dict = self.tree_graph(tree.root)

            for pair in edges:  # merge edge
                list_form = list(pair)
                list_form[0] += shift
                list_form[1] += shift
                edge.append(tuple(list_form))

            edge_list.extend(edge)

            for key in n_dict:  # merge node dict
                node_dict[key + shift] = n_dict[key]
            for key in a_dict:
                arg_dict[key + shift] = a_dict[key]

            root_list[shift] = tree.type

            shift += vertices

        return edge_list, shift, node_dict, arg_dict, root_list

    def tree_graph(self, node, p_index=0, o_index=1):
        edge = []
        node_dict = dict()  # add a dict to find the corresponding node
        arg_dict = dict()
        if not node.o:
            node_dict[p_index] = 'P : A' + str(node.p)
            arg_dict[p_index] = self.original_arg[node.p]

        for o in node.o:
            edge.append((p_index, o_index))
            node_dict[p_index] = 'P : A' + str(node.p)
            arg_dict[p_index] = self.original_arg[node.p]
            node_dict[o_index] = 'O : A' + str(o)
            arg_dict[o_index] = self.original_arg[o]

            new_node = node.children.get(o)
            if new_node:
                sub_p_index = o_index + 1
                edge.append((o_index, sub_p_index))
                node_dict[sub_p_index] = 'P : A' + str(new_node.p)
                arg_dict[sub_p_index] = self.original_arg[new_node.p]

                if new_node.o:
                    sub_edge, o_index, n_dict, a_dict = self.tree_graph(new_node, sub_p_index, sub_p_index + 1)
                    edge.extend(sub_edge)
                    node_dict.update(n_dict)
                    arg_dict.update(a_dict)
                else:
                    end_index = sub_p_index + 1
                    edge.append((sub_p_index, end_index))
                    node_dict[end_index] = new_node.end
                    o_index = end_index + 1
            else:
                end_index = o_index + 1
                edge.append((o_index, end_index))
                node_dict[end_index] = node.end
                o_index = end_index + 1

        return edge, o_index, node_dict, arg_dict


class Node:
    def __init__(self, proponent, opponent, parent, end):
        self.p = proponent
        self.o = opponent
        self.parent = parent
        self.children = dict()
        self.end = end


class DisputeTree:
    def __init__(self, root, leaf):
        self.root = Node(root, leaf, None, False)
        self.layer = [[self.root]]
        self.current_layer = 0
        self.p_set = {root}
        self.o_set = leaf
        self.type = None

# if __name__ == "__main__":
# kb1 = [Or("q", If("r", "s")),
#        If(If("r", If("r", "s")), Or("t", "u")),
#        And(If("t", "q"), If("u", "v")), If("q", "v"), Or("q", "v")]
#
# kb2 = ["a", If("a", "b"), Not("b")]
#
# import pandas as pd
# import re
#
# file_path = '../debate kb.csv'
#
# title = pd.read_csv(file_path, nrows=1, header=None)
#
# df = pd.read_csv(file_path, header=1)

# support_list = []
# claim_list = []
#
# for clause_type, clause in zip(df['Type'], df['Proposition']):
#     if not clause_type.startswith('Norm'):
#         claim_list.append(clause)
#     support_list.append(clause)

# def find_relatives(support_list, claim):
#     literals = re.findall(r'([a-z])', claim)
#
#     while True:
#         pattern = '([' + ''.join(literals) + '])'
#         a_list = [item for item in support_list if re.findall(pattern, item)]
#         n_literals = re.findall(r'([a-z])', ''.join(a_list))
#         if set(n_literals) == set(literals):
#             break
#         else:
#             literals = list(set(n_literals))
#
#     return a_list

# print(find_relatives(support_list, 'p'))

# rela = [(5, 0), (5, 11), (6, 1), (6, 12), (7, 2), (7, 13), (7, 16), (8, 2), (8, 13), (8, 16), (9, 3), (9, 14),
#         (10, 4), (10, 15), (11, 5), (11, 6), (11, 8), (11, 9), (11, 10), (12, 5), (12, 6), (12, 8), (12, 9),
#         (12, 10), (13, 5), (13, 6), (13, 8), (13, 9), (13, 10), (14, 5), (14, 6), (14, 8), (14, 9), (14, 10),
#         (15, 5), (15, 6), (15, 8), (15, 9), (15, 10), (16, 7)]
#
# print()
# extt = Extensions(list(range(17)),rela)
# print(extt.ideal)

# a, b = FindArgument(df).find_all('r>~a')
# print(a)
# print(b)
#
# d = Extensions(a, b)
# # d = Extensions(['a', 'b', 'c', 'd', 'e', 'f', 'g'],[(0, 1), (1, 2), (3, 4), (3, 5), (4, 3), (4, 5), (5, 6), (6, 5)])
# print(d.admissible_extension())
#
# print(d.grounded_extension())
#
# print(d.ideal_extension())

# import igraph
# import plotly.graph_objects as go
#
#
# def dialogical_graph(extension, arg_number):
#     edges, vertices, node_dict, arg_dict, root_dict = extension.dialogical_explanations(arg_number)
#
#     g = igraph.Graph()
#     g.add_vertices(vertices)
#     g.add_edges(edges)
#     graph_layout = g.layout('rt', root=[key for key in root_dict])
#     position = {k: graph_layout[k] for k in range(vertices)}
#     Xn = [position[k][0] for k in range(vertices)]
#     Yn = [-position[k][1] for k in range(vertices)]
#     Xe = []
#     Ye = []
#     for E in edges:
#         Xe += [position[E[0]][0], position[E[1]][0], None]
#         Ye += [-position[E[0]][1], -position[E[1]][1], None]
#
#     node_labels = [node_dict.get(k) for k in range(vertices)]
#
#     hover_labels = [arg_dict.get(k) if arg_dict.get(k) else node_dict.get(k) for k in range(vertices)]
#
#     p_o_color = []
#     for k in range(vertices):
#         if node_dict.get(k).startswith('P'):
#             p_o_color.append('#6175c1')
#         elif node_dict.get(k).startswith('O'):
#             p_o_color.append('#DB4551')
#         else:
#             p_o_color.append('#FCBA12')
#
#     fig = go.Figure()
#
#     fig.add_trace(go.Scatter(x=Xe,
#                              y=Ye,
#                              mode='lines',
#                              line=dict(color='rgb(210,210,210)', width=1),
#                              hoverinfo='none'
#                              ))
#     fig.add_trace(go.Scatter(x=Xn,
#                              y=Yn,
#                              mode='text',
#                              textfont=dict(size=12, color=p_o_color),
#                              text=node_labels,
#                              hovertext=hover_labels,
#                              hoverlabel=dict(bgcolor=p_o_color),
#                              hoverinfo='text',
#                              ))
#
#     axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
#                 zeroline=False,
#                 showgrid=False,
#                 showticklabels=False,
#                 )
#     fig.update_layout(title='Dialogical Explanations',
#                       font_size=12,
#                       autosize=True,
#                       # legend=dict(font=dict(size=10), orientation="h"),
#                       showlegend=False,
#                       xaxis=axis,
#                       yaxis=axis,
#                       margin=dict(l=20, r=20, b=20, t=40),
#                       hovermode='closest',
#                       plot_bgcolor="#F9F9F9",
#                       paper_bgcolor="#F9F9F9",
#
#                       )
#     for key in root_dict:
#         fig.add_annotation(x=position[key][0],
#                            y=-position[key][1],
#                            text=root_dict[key],
#                            showarrow=False,
#                            yshift=50,
#                            font=dict(color='rgb(0,0,0)', size=20))
#
#     fig.show()
#     return fig
#
#
# dialogical_graph(d, 0)

# def make_annotations(pos, text, font_size=20, font_color='rgb(250,250,250)'):
#     if len(text) != len(pos):
#         raise ValueError('The lists pos and text must have the same len')
#     annotations = []
#     for k in range(len(pos)):
#         annotations.append(
#             dict(
#                 text=text[k],  # or replace labels with a different list for the text within the circle
#                 x=pos[k][0], y=-position[k][1],
#                 xref='x1', yref='y1',
#                 font=dict(color=font_color, size=font_size),
#                 showarrow=False)
#         )
#     return annotations
