from RestructureRule import RestructureRule
from nltk import Tree
import argparse
import json


def visualize(args):
    paths = args.paths

    # load each path into list
    loaded = []
    for path in paths:
        with open(path, "r") as file:
            loaded.append(json.load(file))

    res = []
    for element in loaded:
        if RestructureRule.isDictRestructureRule(element):
            rr = RestructureRule.fromDict(element)
            res.append(Tree("Pattern", [rr._patternWithRules()]))
            res.append(Tree("Target", [rr.target]))
        elif isinstance(element, list) and not isinstance(element[0], str):
            # Probably a result dump
            m = ["Multiple"]
            m.extend(element)
            res.append(RestructureRule.treeFromList(m))
        else:
            res.append(RestructureRule.treeFromList(["Tree", element]))

    Tree("Visualizations", res).draw()


parser = argparse.ArgumentParser(
    description="Visualize trees and rules next to each other through nltk.Tree.draw()."
)

parser.add_argument(
    "paths", nargs="+", help="Any number of paths to visualize in a tree."
)


parser.set_defaults(func=visualize)
args = parser.parse_args()
if "func" in vars(args).keys():
    args.func(args)
