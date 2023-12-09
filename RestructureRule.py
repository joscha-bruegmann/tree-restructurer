import ast
from typing import Any
from nltk import Tree
import TreeRestructureFunctions as trf
import json
import re


class RestructureRule:
    """
    Represents a pattern to target transformation rule for trees.

    Instances of this class can be used to set up various rules for restructuring trees,
    based on matching patterns and transferring nodes to a target tree structure.
    """

    pattern: Tree
    target: Tree
    rules: dict[Any, dict]

    def __init__(self, pattern: Tree, target: Tree, rules: dict):
        assert (
            isinstance(pattern, Tree)
            and isinstance(target, Tree)
            and isinstance(rules, dict)
        )
        self.pattern = pattern.copy(deep=True)
        self.target = target.copy(deep=True)
        self.rules = rules

    def applyRule(self, tree: Tree) -> list[Tree]:
        """
        Returns all possible results of applying this RestructureRule on some Tree.
        """
        return trf.transfer(self.pattern, self.target, tree, self.rules)

    @staticmethod
    def isDictRestructureRule(d: dict) -> bool:
        """
        Superficially checks whether a dict contains the necessary keys to
        make a RestructureRule and whether the values are of the appropriate type.
        """
        return (
            isinstance(d, dict)
            and all(x in d.keys() for x in ("Pattern", "Target", "Rules"))
            and isinstance(d["Pattern"], list)
            and isinstance(d["Target"], list)
            and isinstance(d["Rules"], dict)
        )

    @classmethod
    def fromDict(cls, d: dict):
        """
        Make a restructure rule from a dict.

        The dict must contain the keys "Pattern", "Target" and "Rules" with the
        value types list, list and dict respectively.

        "Pattern" and "Target" are expected to be list based tree representations.

        "Rules" is expected to be a dict that specifies for each node in the pattern tree  whether extra child/parent nodes are acceptable for pattern matching and whether to transfer the extra nodes to the target tree.
        """
        # guarding
        if not cls.isDictRestructureRule(d):
            raise ValueError(
                "Path must be a JSON dict with the keys 'Pattern', 'Target' and 'Rules'. The values must be of type list, list and dict respectively."
            )

        # assignment
        pattTree = cls.treeFromList(d["Pattern"])
        targetTree = cls.treeFromList(d["Target"])
        rules: dict = d["Rules"]

        # Reestablish tuples as keys in dict since they were converted by saveAsJson
        # This will involve ast.literal_eval() which at least is safer than eval().
        # It would probably be better to internally use lists instead of tuples and then use json.loads to avoid using ast.
        tupleRe = "(\(\s*\))|(\((\s*\d+\s*,\s*)+(\)|\d+\s*\)))"
        keysToConvert = [
            k for k in rules.keys() if isinstance(k, str) and re.fullmatch(tupleRe, k)
        ]

        for k in keysToConvert:
            v = rules.pop(k)
            convK = ast.literal_eval(k)
            rules[convK] = v

        # nltk.Tree.fromlist will not give you a Tree for a one element list, instead it will give you the first element.
        pattTree = pattTree if isinstance(pattTree, Tree) else Tree(pattTree, [])
        targetTree = (
            targetTree if isinstance(targetTree, Tree) else Tree(targetTree, [])
        )
        return cls(pattTree, targetTree, rules)

    @classmethod
    def fromJsonFile(cls, path: str):
        """
        Make a RestructureRule from a json file.

        The json file must be a dict with the keys "Pattern", "Target" and "Rules" for
        which the value types are list, list and dict respectively.

        "Pattern" and "Target" are expected to be list based tree representations.

        "Rules" is expected to be a dict that specifies for each node in the pattern tree  whether extra child/parent nodes are acceptable for pattern matching and whether to transfer the extra nodes to the target tree.
        """
        with open(path, "r") as file:
            d = json.load(file)

        return cls.fromDict(d)

    # @classmethod
    # def fromString(cls, pattern: str, target: str, brackets: str = "()"):
    #     pass
    #     t = Tree.fromstring(target, brackets)
    #     return cls()

    def saveAsJson(self, path: str):
        """
        Save this rule into a json file at the designated path.
        """
        # Convert rules dict since json object keys have to be strings
        convSet = self.rules.copy()
        convSet = {
            k if not isinstance(k, tuple) else str(k): v
            for k, v in zip(convSet.keys(), convSet.values())
        }

        # Note: Json saves tuples as arrays which will then be loaded as lists.
        with open(path, "w") as file:
            j = json.dump(
                {
                    "Pattern": RestructureRule.treeToList(self.pattern),
                    "Target": RestructureRule.treeToList(self.target),
                    "Rules": convSet,
                },
                file,
                indent=4,
            )

    def _patternWithRules(self):
        """
        Returns a copy of self.pattern with added "ctpt" markings corresponding to
        self.rules.

        This is mainly for visualization purposes.
        """
        vPatt = self.pattern.copy(deep=True)

        for i in [x for x in vPatt.treepositions() if (x in self.rules.keys())]:

            # Generate label
            l = ""
            l += str(vPatt[i].label()) if isinstance(vPatt[i], Tree) else str(vPatt[i])

            def keyExistsAndIsNotEmpty(key):
                return key in self.rules[i].keys() and self.rules[i][key]

            if keyExistsAndIsNotEmpty("targetIndex"):
                l += "\ntarget:" + str(self.rules[i]["targetIndex"])

            matchingRules = "\n"
            if keyExistsAndIsNotEmpty("allowUnspecifiedChildren"):
                matchingRules += "c"
                if keyExistsAndIsNotEmpty("transferUnspecifiedChildren"):
                    matchingRules += "t"
            if keyExistsAndIsNotEmpty("allowUnspecifiedParents"):
                matchingRules += "p"
                if keyExistsAndIsNotEmpty("transferUnspecifiedParents"):
                    matchingRules += "t"

            l += matchingRules if len(matchingRules) >= 2 else ""

            # Apply label
            if isinstance(vPatt[i], Tree):
                vPatt[i].set_label(l)
            else:
                vPatt[i] = l

        return vPatt

    def draw(self):
        """
        Gives a graphical visualization of a RestructureRule instance.

        Uses nltk.Tree.draw
        """
        Tree(
            "Restructure rule",
            [
                Tree("Pattern", [self._patternWithRules()]),
                Tree("Target", [self.target]),
            ],
        ).draw()

    @staticmethod
    def treeToList(tree: Tree) -> list:
        """
        Creates a list based tree representation from an nltk.Tree.

        The result will consist of nested lists where every node is
        of the format [NodeLabel, [child1Label], ..., [childnLabel]]

        A simple tree would thus be represented by:
        ["root", ["Hello"], ["world!", ["foo"], ["bar"]]].
        """
        assert isinstance(tree, Tree)

        def recFun(t):
            if isinstance(t, Tree):
                if len(t) > 0:
                    return [t.label(), *[recFun(c) for c in t]]
                else:
                    return [t.label()]
            else:
                return [t]

        return recFun(tree)

    @classmethod
    def treeFromList(cls, l):
        """
        :type l: list
        :param l: a tree represented as nested lists

        :return: A tree corresponding to the list representation ``l``.
        :rtype: Tree

        Converts nested lists to an NLTK Tree.

        This is an edit of the nltk.Tree.fromlist implementation to fix generation of unintended double quotes.
        """
        if type(l) == list and len(l) > 0:
            # Tree.fromList uses label = repr(l[0]) here which results in the double quotes all over the place.
            # For consideration: maybe do use repr unless type(l[0])==str
            label = l[0]
            if len(l) > 1:
                return Tree(label, [cls.treeFromList(child) for child in l[1:]])
            else:
                return label

    @classmethod
    def treeFromJson(cls, path) -> Tree:
        """
        Creates an nltk.Tree from a list based tree representation in a json file.

        The tree in the json file should consist of nested lists where every node is
        of the format [NodeLabel, [child1Label], ..., [childnLabel]]

        A simple tree would be represented by ["root", ["Hello"], ["world!", ["foo"], ["bar"]]].
        """
        with open(path) as file:
            tree = cls.treeFromList(json.load(file))
        return tree
