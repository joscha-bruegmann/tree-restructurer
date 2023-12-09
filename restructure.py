import json
from RestructureRule import RestructureRule
import argparse
from nltk import Tree


def functionality(args):
    """
    Console interface functionality.
    """
    d = vars(args)

    rule = RestructureRule.fromJsonFile(d["rule-path"])
    tree = RestructureRule.treeFromJson(d["tree-path"])
    results = rule.applyRule(tree)

    # Only convert if necessary.
    _convRes = []

    def resultsConvertedToLists():
        if not _convRes:
            _convRes.extend([RestructureRule.treeToList(e) for e in results])
        return _convRes

    if d["dump"]:
        with open(d["dump"], "w") as outpath:
            json.dump(resultsConvertedToLists(), outpath, indent=4)
    if d["visualize"]:
        Tree("Results", results).draw()

    # Console output
    if d["quiet"]:
        return
    # elif d["print_lists"]:
    #     convRes = RestructureRule._treeAsList(results) if not convRes else convRes
    #     print(json.dumps(convRes))
    elif d["pretty_print"]:
        for e in results:
            e.pretty_print()
    else:
        print(json.dumps(resultsConvertedToLists()))


parser = argparse.ArgumentParser(
    description="""Given some tree, outputs all possible results of applying the given rule 
    in a JSON compatible list.
    For details on the format of the json files, check the readme.
    """
)
# subparsers = parser.add_subparsers()
#
# applicationsParser = subparsers.add_parser(
#     "applications",
#     help="Generate the possibilities of how a RestructureRule can apply.",
# )
parser.add_argument(
    "tree-path",
    help="""Path to the JSON file of the tree to apply the rule on.
    The JSON file should consist of nested lists forming a tree.""",
)
parser.add_argument("rule-path", help="Path to the JSON file of the rule to apply.")
parser.add_argument(
    "--dump",
    help="Writes the results to a given path.",
)
parser.add_argument(
    "--visualize",
    action="store_true",
    help="Will visualize the results using nltk.Tree.draw().",
)
mgroup = parser.add_mutually_exclusive_group()
mgroup.add_argument(
    "--pretty-print",
    action="store_true",
    help="""Will show ASCII or Unicode art of the resulting trees. 
    CAUTION: this may not be accurate.""",
)
# mgroup.add_argument(
#     "--print-lists",
#     action="store_true",
#     help="Will print the results as nested lists.",
# )
mgroup.add_argument(
    "--quiet", action="store_true", help="Suppresses command line output."
)

parser.set_defaults(func=functionality)
args = parser.parse_args()
if "func" in vars(args).keys():
    args.func(args)
