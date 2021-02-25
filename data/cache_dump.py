import pandas as pd

from argument_engine.argument import *

import json
import ast

# used to store calculated result in order to boost performance


file_path = 'debate kb.csv'

title = pd.read_csv(file_path, nrows=1, header=None)

df = pd.read_csv(file_path, header=1)

extension_dic = dict()
premises_dic = dict()


for row in df.itertuples():

    arguments, relation, separated_set_of_premises = FindArgument(df).find_all(row.proposition, combine=True)

    extension = Extensions(arguments, relation)

    extension_dic[row.proposition] = str(extension.__dict__.copy())

    premises_dic[row.proposition] = separated_set_of_premises


with open('cache_ext.txt', 'w') as cache_file:
    json.dump(extension_dic, cache_file)

with open('cache_premises.txt', 'w') as cache_file:
    json.dump(premises_dic, cache_file)



# with open('cache_ext.txt') as cache_file:
#     ext_dic = json.load(cache_file)
#
#
#
#
#
# claim = '~b'
#
# ext_str = ext_dic[claim].replace('set()', '"empty_set"')    # because ast cannot read set()
#
# raw_ext = ast.literal_eval(ext_str)
#
# for key in raw_ext:
#     if isinstance(raw_ext[key], list):
#         raw_ext[key] = [set() if item == 'empty_set' else item for item in raw_ext[key]]
#     else:
#         if raw_ext[key] == 'empty_set':
#             raw_ext[key] = set()
#
# ext = Extensions.__new__(Extensions)
# ext.__dict__.update(raw_ext)
#
# print(ext.complete_extension())
#

print('ok')
