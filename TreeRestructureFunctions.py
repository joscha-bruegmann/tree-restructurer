from nltk import Tree
from itertools import product

# In my opinion, all of these functions need reworking.
# I should not have used nltk.Tree internally.
# It should also be strongly reconsidered whether to bake the rules into the nodes.
# The functions can definitely be simplified and some stuff may be completely unnecessary.


def _bakeRules(pattern: Tree, rules: dict):
    # I opted for baking the rules dict into the Tree to simplify recursive operation
    # on the tree. There probably is a more elegant solution for this.
    def getRule(rules: dict, nodeIndex, key=None):
        # Absent key should be equivalent to Rule being False
        if key:
            try:
                return rules[nodeIndex][key]
            except KeyError:
                return False
        else:
            try:
                return rules[nodeIndex]
            except:
                return {}

    for pos in pattern.treepositions():
        # print(pos)
        # print(type(pos))
        curr = pattern[pos]
        if isinstance(curr, str):
            # Add node content to rules under 'label' and replace node content with rule dict
            s = getRule(rules, pos)
            s["label"] = curr
            pattern[pos] = s

        # This still needs to be tested
        elif isinstance(curr, dict):
            pattern[pos] |= getRule(rules, pos)

        elif isinstance(curr, Tree):
            s = getRule(rules, pos)
            s["label"] = curr.label()
            pattern[pos].set_label(s)

        else:
            raise TypeError(f"The input tree has an invalid type at {pos}.")


def _getRuleFromNode(node: Tree | dict | str, key):
    try:
        if isinstance(node, Tree):
            if isinstance(node.label(), dict):
                return node.label()[key]
            else:
                return False
        elif isinstance(node, dict):
            return node[key]
        elif isinstance(node, str):
            return False
        else:
            raise TypeError("Function only allows Trees and dict and str for node.")
    except KeyError:
        return False


def findAllInTree(content, tree: Tree):
    labelIndexPairs = [
        (e.label(), i) if isinstance(e, Tree) else (e, i)
        for e, i in [(tree[i], i) for i in tree.treepositions()]
    ]
    res = []
    for p in labelIndexPairs:
        if p[0] == content:
            res.append(p[1])

    return res


def getAssignmentPermutations(A: list, B: list, wildcardsOfA: list):
    """returns a list of sets of permutations of the indices of A and B.\n
    The index of the elements of the set correspond to the index of elements in A and the value in the set for that index corresponds to the index where the element was found in B
    Any results that don't have increasing indices throughout the individual set get filtered out.\n
    Two lists [a, b] and [a, a, b, b, a] would result in a list [(0, 2), (0, 3), (1, 2), (1, 3)]. The tuples (4, 2) and (4, 3) get filtered.
    """

    if len(A) != len(wildcardsOfA):
        raise ValueError("Wildcards doesn't have the appropriate amount of values.")
    if len(A) > len(B):
        return []

    # First get all individually possible positions
    possiblePositions = [[] for _ in A]
    for i in range(len(A)):
        for j in range(i, len(B) - (len(A) - i - 1)):
            # Anything before i and after len(B)-(len(A)-i-1)
            # couldn't be part of a permutation
            if A[i] == B[j] or wildcardsOfA[i]:
                possiblePositions[i].append(j)

    # I think the product is what I want...
    p = product(*possiblePositions)
    # Throw out any result that doesn't follow the order of occurence.
    res = []
    for l in p:
        b = True
        c = -1
        for i in l:
            if i <= c:
                b = False
                break
            else:
                c = i
        if b:
            res.append(l)

    return res


# # This is messy, complicated and needs clean up.
# def doesPatternApply(pattern: Tree | dict, tree: Tree | str) -> bool:
#     patternLabel = _getRuleFromNode(pattern, "label")
#     allowUnspecifiedParents = _getRuleFromNode(pattern, "allowUnspecifiedParents")
#     allowUnspecifiedChildren = _getRuleFromNode(pattern, "allowUnspecifiedChildren")

#     # region Leaf handling:
#     # I can probably integrate this into the bottom stuff...
#     # If pattern is leaf
#     if isinstance(pattern, dict) or (isinstance(pattern, Tree) and len(pattern) == 0):
#         # and tree is leaf
#         if isinstance(tree, str):
#             # Flags for unspecified don't matter at this point since
#             # there are no children to ignore and no subtrees to check
#             return patternLabel == tree
#         # or tree has no children
#         elif isinstance(tree, Tree) and len(tree) == 0:
#             return patternLabel == tree.label()

#         # If tree has children
#         elif isinstance(tree, Tree):
#             if allowUnspecifiedParents:
#                 candidates = findAllInTree(patternLabel, tree)
#                 if allowUnspecifiedChildren:
#                     # If unspecified children are allowed, any candidate will do.
#                     return len(candidates) > 0
#                 elif not allowUnspecifiedChildren:
#                     # If unspecified children are not allowed, any candidate that
#                     # is a leaf will do.
#                     for c in [tree[i] for i in candidates]:
#                         if isinstance(c, str) or (isinstance(c, Tree) and len(c) == 0):
#                             return True
#                     return False

#             elif not allowUnspecifiedParents:
#                 # At this point tree *has* children and pattern is a leaf,
#                 # Since pattern is a leaf, pattern doesn't specify children.
#                 # Unless unspecified children are allowed, no children are allowed.
#                 # Since tree does have children, allowUnspecifiedChildren has to be
#                 # True for this code path to return true.
#                 return allowUnspecifiedChildren and patternLabel == tree.label()

#     # If pattern has children and tree is a leaf return False since pattern can't apply
#     elif (isinstance(pattern, Tree) and len(pattern) > 0) and (
#         isinstance(tree, str) or (isinstance(tree, Tree) and len(tree) == 0)
#     ):
#         return False
#     # endregion
#     # Only cases where both are Trees with children are left now

#     # While I don't really like using local functions within functions,
#     # I didn't want to have identical copies. Also this is too
#     # dependent on other local variables to extract into a proper one.
#     # I might think about a cleaner way later...
#     def unspecifiedChildrenAllowed(pattern, tree):
#         patternDirectChildren = [_getRuleFromNode(e, "label") for e in pattern]
#         allowUndesignatedParentList = [
#             _getRuleFromNode(e, "allowUnspecifiedParents") for e in pattern
#         ]
#         treeDirectChildren = [e.label() if isinstance(e, Tree) else e for e in tree]
#         # I need to figure out a combination of me assigning my children
#         # to nodes in tree that makes my children happy.
#         if len(patternDirectChildren) > len(treeDirectChildren):
#             return False

#         permutations = getAssignmentPermutations(
#             patternDirectChildren, treeDirectChildren, allowUndesignatedParentList
#         )

#         # check permutations for one that is accepted by all children of pattern
#         for p in permutations:
#             # check if each child is ok at the spot that is designated by permutation
#             acceptable = True
#             for i in range(len(pattern)):
#                 if not doesPatternApply(pattern[i], tree[p[i]]):
#                     acceptable = False
#                     break
#             if acceptable:
#                 return True
#         return False

#     def unspecifiedChildrenNotAllowed(pattern, tree):
#         patternDirectChildren = [_getRuleFromNode(e, "label") for e in pattern]
#         treeDirectChildren = [e.label() if isinstance(e, Tree) else e for e in tree]

#         if len(patternDirectChildren) != len(treeDirectChildren):
#             return False
#         for i in range(len(patternDirectChildren)):
#             if not doesPatternApply(pattern[i], tree[i]):
#                 return False
#         return True

#     if allowUnspecifiedParents:
#         candidates = findAllInTree(patternLabel, tree)
#         if allowUnspecifiedChildren:
#             for c in candidates:
#                 if c == ():
#                     if unspecifiedChildrenAllowed(pattern, tree):
#                         return True
#                 else:
#                     if doesPatternApply(pattern, tree[c]):
#                         return True
#             return False

#         elif not allowUnspecifiedChildren:
#             for c in candidates:
#                 if c == ():
#                     if unspecifiedChildrenNotAllowed(pattern, tree):
#                         return True
#                 else:
#                     if doesPatternApply(pattern, tree[c]):
#                         return True
#             return False

#     elif not allowUnspecifiedParents:
#         if allowUnspecifiedChildren:
#             return unspecifiedChildrenAllowed(pattern, tree)

#         elif not allowUnspecifiedChildren:
#             return unspecifiedChildrenNotAllowed(pattern, tree)

#     # If this is reached some path isn't returning a value.
#     assert (
#         False
#     ), "This should not have been reached. Some path in this function is not returning a value."


# returning trees may not be safe to edit
# expects settings to be baked into tree
def howCanPatternApply(
    pattern: Tree | dict, tree: Tree | str, _pattindx=(), _treeindx=()
):
    patternLabel = _getRuleFromNode(pattern, "label")
    allowUnspecifiedParents = _getRuleFromNode(pattern, "allowUnspecifiedParents")
    allowUnspecifiedChildren = _getRuleFromNode(pattern, "allowUnspecifiedChildren")

    # I can probably integrate this into the bottom stuff...
    # If pattern is leaf
    if isinstance(pattern, dict) or (isinstance(pattern, Tree) and len(pattern) == 0):
        # and tree is leaf
        if isinstance(tree, str):
            if patternLabel == tree:
                return ("I am at", _pattindx, _treeindx)
            else:
                return []
        # or tree has no children
        elif isinstance(tree, Tree) and len(tree) == 0:
            if patternLabel == tree.label():
                return ("I am at", _pattindx, _treeindx)
            else:
                return []

        # If tree has children
        elif isinstance(tree, Tree):
            if allowUnspecifiedParents:
                candidates = findAllInTree(patternLabel, tree)

                if allowUnspecifiedChildren:
                    # If unspecified children are allowed, any candidate will do.
                    if len(candidates) == 1:
                        return ("I am at", _pattindx, (*_treeindx, *candidates[0]))
                    elif len(candidates) > 1:
                        return (
                            "options",
                            [
                                ("I am at", _pattindx, (*_treeindx, *x))
                                for x in candidates
                            ],
                        )
                    else:
                        return []

                elif not allowUnspecifiedChildren:
                    # If unspecified children are not allowed, any candidate that
                    # is a leaf will do.
                    acceptable = []
                    for i in candidates:
                        c = tree[i]
                        if isinstance(c, str) or (isinstance(c, Tree) and len(c) == 0):
                            acceptable.append(("I am at", _pattindx, (*_treeindx, *i)))
                    if len(acceptable) > 1:
                        return ("options", acceptable)
                    elif len(acceptable) == 1:
                        return acceptable[0]
                    else:
                        return []

            elif not allowUnspecifiedParents:
                # At this point tree has children and pattern is a leaf,
                if allowUnspecifiedChildren and patternLabel == tree.label():
                    # this return value was wrapped in a list before but that seemed wrong...
                    # I'm pretty sure I left that wrapping in by mistake and missed it when I fixed
                    # this bug before.
                    return ("I am at", _pattindx, _treeindx)
                else:
                    return []

    # If pattern has children and tree is a leaf return False since pattern can't apply
    elif (isinstance(pattern, Tree) and len(pattern) > 0) and (
        isinstance(tree, str) or (isinstance(tree, Tree) and len(tree) == 0)
    ):
        return []
    # Only cases where both are Trees with children should be left now
    assert isinstance(pattern, Tree) and isinstance(
        tree, Tree
    ), "Only cases where both are Trees with children should be left now. What did I miss?"

    def unspecifiedChildrenAllowed(
        pattern: Tree, tree: Tree, _pattindx=(), _treeindx=()
    ):
        patternDirectChildren = [_getRuleFromNode(e, "label") for e in pattern]
        allowUndesignatedParentList = [
            _getRuleFromNode(e, "allowUnspecifiedParents") for e in pattern
        ]
        treeDirectChildren = [e.label() if isinstance(e, Tree) else e for e in tree]
        # I need to figure out a combination of me assigning my children
        # to nodes in tree that makes my children happy.
        if len(patternDirectChildren) > len(treeDirectChildren):
            return []

        permutations = getAssignmentPermutations(
            patternDirectChildren, treeDirectChildren, allowUndesignatedParentList
        )

        res = []
        # check permutations for the ones that are accepted by all children of pattern
        for p in permutations:
            # check if each child is ok at the spot that is designated by permutation
            acceptable = []
            for i in range(len(pattern)):
                childTrace = howCanPatternApply(
                    pattern[i], tree[p[i]], (*_pattindx, i), (*_treeindx, p[i])
                )
                if childTrace:
                    acceptable.extend(
                        childTrace if isinstance(childTrace, list) else (childTrace,)
                    )
                else:
                    acceptable = []
                    break
            if acceptable:
                # trying this to see if this is just a special case:
                if (
                    len(acceptable) == 1
                    and isinstance(acceptable[0], tuple)
                    and acceptable[0][0] == "options"
                ):
                    res.extend(
                        [
                            ("I have children", ("I am at", _pattindx, _treeindx), [e])
                            for e in acceptable[0][1]
                        ]
                    )
                else:
                    # It seemed like there being exactly one acceptable permutation that is "options" was a special case
                    # of allowing unspecified parents. Let's see if this holds
                    assert not [x for x in acceptable[1:] if x[0] == "options"]
                    res.append(
                        (
                            "I have children",
                            ("I am at", _pattindx, _treeindx),
                            acceptable,
                        )
                    )
        # res should now be a list of where my children can be where my children provided lists of where their children can be. ## Stroke?
        # This comment is a perfect example of how hard trying to explain the workings of a program while staying intelligible can be.
        if len(res) > 1:
            return ("options", res)
        elif len(res) == 1:
            return res[0]
        else:
            return []

    def unspecifiedChildrenNotAllowed(pattern, tree, _pattindx=(), _treeindx=()):
        patternDirectChildren = [_getRuleFromNode(e, "label") for e in pattern]
        treeDirectChildren = [e.label() if isinstance(e, Tree) else e for e in tree]

        if len(patternDirectChildren) != len(treeDirectChildren):
            return []

        res = []

        # check that all children return a non empty list
        for i in range(len(patternDirectChildren)):
            res.append(
                howCanPatternApply(
                    pattern[i], tree[i], (*_pattindx, i), (*_treeindx, i)
                )
            )
            if not res[i]:
                return []

        return ("I have children", ("I am at", _pattindx, _treeindx), res)

    if allowUnspecifiedParents:
        candidates = findAllInTree(patternLabel, tree)
        res = []
        for c in candidates:
            if c == ():
                if allowUnspecifiedChildren:
                    canIBeHere = unspecifiedChildrenAllowed(
                        pattern, tree, _pattindx, _treeindx
                    )
                else:
                    canIBeHere = unspecifiedChildrenNotAllowed(
                        pattern, tree, _pattindx, _treeindx
                    )
                if canIBeHere and not canIBeHere in res:
                    res.append(canIBeHere)
            else:
                a = howCanPatternApply(pattern, tree[c], _pattindx, (*_treeindx, *c))
                if a and not a in res:
                    res.append(a)

        if len(res) > 1:
            return ("options", res)
        elif len(res) == 1:
            return res[0]
        else:
            return []

    elif not allowUnspecifiedParents:
        if _getRuleFromNode(pattern, "label") != tree.label():
            return []

        if allowUnspecifiedChildren:
            return unspecifiedChildrenAllowed(pattern, tree, _pattindx, _treeindx)
        else:
            return unspecifiedChildrenNotAllowed(pattern, tree, _pattindx, _treeindx)

    # If this is reached some path isn't returning a value.
    assert (
        False
    ), "This should not have been reached. Some path in this function is not returning a value."


def patternApplications(pattern: Tree, tree: Tree, rules=None):
    if rules:
        _bakeRules(pattern, rules)
        # Otherwise tree is expected to be baked.

    l = howCanPatternApply(pattern, tree)
    if not l:
        return []

    def rec(tpl: tuple, _parentIndexInTree=()) -> list | Tree:
        assert (
            isinstance(tpl, tuple)
            and (
                len(tpl) == 3
                and tpl[0] == "I am at"
                and isinstance(tpl[1], tuple)
                and isinstance(tpl[2], tuple)
            )
            or (
                len(tpl) == 3
                and tpl[0] == "I have children"
                and isinstance(tpl[1], tuple)
                and isinstance(tpl[2], list)
            )
            or (len(tpl) == 2 and tpl[0] == "options" and isinstance(tpl[1], list))
        )

        # Leaf
        if tpl[0] == "I am at":
            # pLoc is where the node is in pattern. _parentIndexInTree is where the parent in pattern is in the tree.
            # Since I might need to get the intermediate tree between this node and the parent in pattern.
            pLoc = tpl[1]
            treeLoc = tpl[2]
            transferChildren = _getRuleFromNode(
                pattern[pLoc], "transferUnspecifiedChildren"
            )
            transferParents = _getRuleFromNode(
                pattern[pLoc], "transferUnspecifiedParents"
            )

            # Copy whole tree, change what I need, return what I want
            # results in a lot of memory waste but its an easy solution
            tc = tree.copy(deep=True)
            if not transferChildren and isinstance(tc[treeLoc], Tree):
                tc[treeLoc].clear()

            # The solution to the bug caused by this segment was that this case was already handled in an upper level...
            # Therefore this bit of code was trying to do something that it didn't even need to do...
            # The bug this caused was duplicate trees.
            # # A bit frustrating that 'x is not None' and 'not (x is None)' are equivalent
            # if transferParents:
            #     if _parentIndexInTree is not None:
            #         # transfer = tc[treeLoc[: len(_parentIndexInTree) + 1]]
            #         transfer = tc[
            #             (*_parentIndexInTree, treeLoc[len(_parentIndexInTree)])
            #         ]
            #     else:
            #         transfer = tc
            # else:
            #     transfer = tc[treeLoc]
            transfer = tc[treeLoc]

            assert type(transfer) in [str, Tree]
            s = {
                "label": transfer.label() if isinstance(transfer, Tree) else transfer,
                "targetIndex": _getRuleFromNode(pattern[pLoc], "targetIndex"),
                "myIndexInParentsList": treeLoc[len(_parentIndexInTree) :]
                if _parentIndexInTree is not None
                else None,
            }
            if isinstance(transfer, Tree):
                transfer.set_label(s)
            else:
                transfer = Tree(s, [])

            return transfer

        # Tree
        elif tpl[0] == "I have children":
            pLoc = tpl[1][1]
            treeLoc = tpl[1][2]
            transferChildren = _getRuleFromNode(
                pattern[pLoc], "transferUnspecifiedChildren"
            )
            transferParents = _getRuleFromNode(
                pattern[pLoc], "transferUnspecifiedParents"
            )

            # Get unspecified parent tree
            tc = tree.copy(deep=True)
            me = tc[treeLoc]
            # I had more tree duplication like in the leaf clause, so I just got rid of this.
            # Seems to have fixed it.
            # # if not transferChildren and isinstance(tc[treeLoc], Tree):
            # #     tc[treeLoc].clear()
            # if transferParents:
            #     transfer = tc[treeLoc[: len(_parentIndexInTree)]]
            # else:
            #     transfer = me

            transfer = me

            myPosInTransfer = treeLoc[len(_parentIndexInTree) :]

            transfer.set_label(
                {
                    "label": transfer.label(),
                    "targetIndex": _getRuleFromNode(pattern[pLoc], "targetIndex"),
                    "myIndexInParentsList": myPosInTransfer  # treeLoc[len(_parentIndexInTree) + 1]
                    if _parentIndexInTree is not None
                    else None,
                }
            )

            # If I need to edit my children: edit *me*
            # If I need to copy the tree that is supposed to be returned; copy *transfer*

            # If me has no children in tree, the child management that follows doesn't matter
            if not isinstance(me, Tree):
                return transfer

            # indicesOfChildrenToWipe = [range(len(tree[treeLoc]))]
            processedChildren = [rec(child, treeLoc) for child in tpl[2]]

            assert not [
                x for x in processedChildren if type(x) not in [Tree, list, dict]
            ], "Children list contains unexpected type."

            # Keeping the indices and deleting them later ended up being unnecessary since I don't need to handle permutations here.
            indicesOfChildrenToKeep = []
            # replace definite children
            for c in [x for x in processedChildren if type(x) in [Tree, dict]]:
                indexInParent = _getRuleFromNode(c, "myIndexInParentsList")
                assert indexInParent, "This is a child, it has to have a parent."
                # keep track of which children to keep in case unspecified children aren't transferred
                indicesOfChildrenToKeep.append(indexInParent[0])
                me[indexInParent] = c

            # # Try this later
            # possibilities = []
            # keepIPerPossibility=[]
            # # get possibilities caused by indefinite children
            # for c in [x for x in processedChildren if isinstance(x, list)]:

            #     pass

            # I think doing it like this ended up being unnecessary
            # Delete unspecified children afterwards
            # Depending on how the pattern was matched in each option, which children are part of
            # the match is dependent on the option. I keep all original children at first so they can be copied
            # and then delete the ones that aren't part of the match afterwards, if necessary.
            if not transferChildren:
                deletions = 0
                for i in range(len(me)):
                    if i not in indicesOfChildrenToKeep:
                        s = i - deletions
                        me[s : s + 1] = []
                        deletions += 1

            return transfer

            # if not transferChildren:
            #     # wipe all children in indexOfChildrenToWipe from result trees
            #     pass

            # # Get children that matched
            # for child in list[2]:
            #     processedChild = rec(child, treeLoc)
            #     # If there is options
            #     if isinstance(processedChild, list):
            #         # make tree for each child option and set copies of this node as their parents
            #         # get all options as a list
            #         res.append()
            #     else:
            #         if transferChildren:
            #             # do it by index
            #             pass
            #         else:
            #             fj = transfer.copy(deep=True)
            #             fj.append(processedChild)
            #             res.append(fj)

            # Get unspecified children for each option in the list

        # Possibilities
        elif tpl[0] == "options":
            # consume lower levels
            res = []
            for x in tpl[1]:
                c = rec(x)
                assert type(c) in [list, Tree, dict]
                res.extend((c,) if type(c) in [Tree, dict] else c)
            return res

        assert False, "Some paths aren't returning a value"

    return rec(l)


def transfer(pattern: Tree, target: Tree, tree: Tree, rules: dict = None) -> list[Tree]:
    pa = patternApplications(pattern.copy(deep=True), tree, rules)
    pa = [pa] if isinstance(pa, Tree) else pa

    res = []
    for t in pa:
        targetCopy = target.copy(deep=True)
        # sorting this list so I can remove childhood relationships from leaf up.
        # This way I won't lose access to references via indices.
        posSorted = [
            e
            for e in t.treepositions()
            if type(_getRuleFromNode(t[e], "targetIndex")) in (tuple, list)
        ]
        posSorted.sort(key=len, reverse=True)
        toTransfer = [t[e] for e in posSorted]
        # assert not [x for x in toTransfer if not getRuleFromNode(x, "label")]

        # Separate children from parents (this sounds wrong...) so they don't show up multiple times in target
        # count deletions per parent so I can adjust the indices needed for slicing
        deletions = {}
        for i in posSorted:
            if len(i) == 0:
                break
            pi = i[:-1]
            parent = t[pi]
            if pi not in deletions.keys():
                deletions[pi] = 0
            parent[i[-1] - deletions[pi] : i[-1] - deletions[pi] + 1] = []
            deletions[pi] += 1

        # point indices to correct snips
        for i in toTransfer:
            ti = _getRuleFromNode(i, "targetIndex")
            l = _getRuleFromNode(i, "label")

            if isinstance(i, Tree):
                i.set_label(l)
            else:
                i = l

            # Since json doesn't differentiate between lists and tuples I'll check by nesting
            # depth instead of type.
            # targetIndex must be a list/tuple of ints or a list containing lists/tuples of ints
            if not (
                all(isinstance(f, int) for f in ti)
                or all(
                    type(e) in (tuple, list) and all(isinstance(j, int) for j in e)
                    for e in ti
                )
            ):
                raise Exception(
                    "Invalid target index format; check your Rule JSON file."
                )

            ti = ti if len(ti) > 0 and type(ti[0] in (list, tuple)) else [ti]
            for tt in ti:
                if isinstance(targetCopy[tt], Tree):
                    targetCopy[tt].extend(i)
                    targetCopy[tt].set_label(l)
                elif isinstance(targetCopy[tt], str):
                    targetCopy[tt] = i
                else:
                    raise ValueError

        # clean up dicts
        for i in targetCopy.treepositions():
            te = targetCopy[i]
            if isinstance(te, Tree):
                if isinstance(te.label(), dict):
                    te.set_label(_getRuleFromNode(te, "label"))
            elif isinstance(te, dict):
                targetCopy[i] = _getRuleFromNode(te, "label")

        res.append(targetCopy)

    # resTree = Tree("Results", res)
    return res
