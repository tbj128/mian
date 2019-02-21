import csv
import sys
from collections import defaultdict
from pprint import pprint

def tree(): return defaultdict(tree)

def tree_add(t, path):
    i = 0
    for node in path:
        if i > 0:
            t = t[node]
        i += 1
    t = t[path[0]]

def pprint_tree(tree_instance):
    def dicts(t): return {k: dicts(t[k]) for k in t}
    pprint(dicts(tree_instance))

def save_tree(tree_instance, csv_path):
    with open(csv_path, "w") as text_file:
        text_file.write(tree_instance)

def csv_to_tree(input):
    t = tree()
    i = 0
    with open(input, 'r') as csvfile:
        for row in csv.reader(csvfile, delimiter='\t', quotechar='\''):
            if i > 0:
                tree_add(t, row)
            i += 1
    return t

def tree_to_newick(root):
    items = []
    for k,v in root.items():
        s = ''
        is_lowest = False
        if len(root[k].keys()) > 0:
            sub_tree = tree_to_newick(root[k])
            if sub_tree != '':
                s += '(' + sub_tree + ':1)'
        else:
            is_lowest = True
        s += k
        if is_lowest:
            items.append("'" + s + "'")
        else:
            items.append(s)

    return ':1,'.join(items)

def csv_to_weightless_newick(input):
    t = csv_to_tree(input)
    out = tree_to_newick(t) + ":1;"
    return out

save_tree(csv_to_weightless_newick(sys.argv[1]), sys.argv[2])
