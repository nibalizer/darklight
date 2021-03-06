# Copyright 2008 Corbin Simpson
# <cds@corbinsimpson.com>
# This code is provided under the terms of the GNU Public License, version 3.

import itertools
import os

import tiger

def grouper(n, iterable):
    "grouper(3, 'ABCDEFG') --> ABC DEF"
    args = [iter(iterable)] * n
    return itertools.izip(*args)

class Branch(object):
    """
    Helper class for describing binary trees.

    Nodes can be cut off at any point to form a complete tree.
    """

    offset = 0
    """
    Offset of this branch in the file.

    Only makes sense if the branch is a leaf.
    """

    def __init__(self, left=None, right=None, is_leaf=False, thex=True):
        self.left = left
        self.right = right
        self.is_leaf = is_leaf

        if left and right and not is_leaf:
            # Branch.
            buf = left.hash + right.hash
            if thex:
                buf = "\x01%s" % buf
            self.hash = tiger.tiger(buf).digest()
            self.size = left.size + right.size
        elif is_leaf and left:
            # Leaf.
            self.size = left.size
            self.hash = left.hash

    def __eq__(self, other):
        return self.size == other.size and self.hash == other.hash

    def __repr__(self):
        return "<Branch(%s, %d)%s>" % (self.hash.encode("hex"), self.size,
            " (leaf)" if self.is_leaf else "")

    @classmethod
    def as_incomplete(cls, size, hash, **kwargs):
        """
        Make an incomplete branch node.
        """

        self = cls(**kwargs)
        self.size = size
        self.hash = hash

        return self

class TTH(object):
    """A class describing a Tiger Tree Hash tree."""

    top = None
    """
    The top of the tree.

    May be None if the tree has not been initialized.
    """

    complete = False
    """
    Whether this tree is complete.

    Completed trees have leaves for every single block in the object they have
    hashed.
    """

    def __init__(self, thex=False, maxlevels=0, blocksize=128 * 1024):
        self.thex = thex

        if self.thex:
            self.blocksize = 1024
        else:
            self.blocksize = blocksize

    @classmethod
    def from_size_and_hash(cls, size, hash, **kwargs):
        """
        Create an incomplete tree from a size and a hash.

        The tree may end up being complete if it only has one node.
        """

        self = cls(**kwargs)
        if size > self.blocksize:
            self.top = Branch.as_incomplete(size, hash, thex=self.thex)
            self.complete = False
        else:
            self.top = Branch.as_incomplete(size, hash, thex=self.thex,
                is_leaf=True)
            self.complete = True

        return self

    def is_complete(self, branch):
        if branch.is_leaf:
            return True
        if branch.left:
            if branch.right:
                return True
            if self.blocksize <= branch.size:
                return True
        return False

    def iter_branches(self):
        """
        Yield every branch (and leaf) in the tree, in no particular order.

        The order is actually currently a left-to-right depth-first traversal,
        but that shouldn't matter.
        """

        stack = [self.top]

        while stack:
            current = stack.pop()
            if current.left:
                stack.append(current.left)
            if current.right:
                stack.append(current.right)
            yield current

    def iter_incomplete_branches(self):
        """
        Get a list of branches which have incomplete children.

        This method goes through the entire tree regardless of whether it is
        marked as complete.
        """

        for branch in self.iter_branches():
            if not self.is_complete(branch):
                yield branch

    def extend_branch(self, branch, data):
        """
        Extend a branch using data from the network.
        """

        left = Branch.as_incomplete(data["first_size"], data["first_hash"],
            thex=self.thex)
        if left.size <= self.blocksize:
            left.is_leaf = True
        right = Branch.as_incomplete(data["second_size"],
            data["second_hash"], thex=self.thex)
        if right.size <= self.blocksize:
            right.is_leaf = True

        if not branch.left:
            branch.left = left
        if not branch.right:
            branch.right = right

        if not any(self.iter_incomplete_branches()):
            self.complete = True

    def update_offsets(self):
        """
        Set up the offsets for each of the leaves.
        """

        if not self.complete:
            return

        offset = 0
        for branch in self.iter_branches():
            if branch.is_leaf:
                branch.offset = offset
                offset += branch.size

    def build_tree_from_path(self, f):
        """
        Build a complete tree by hashing a file.
        """

        if os.stat(f).st_size:
            h = open(f, "rb")
            leaves = []
            buf = h.read(self.blocksize)
            while len(buf):
                size = len(buf)
                if self.thex:
                    buf = '\x00' + buf
                leaves.append((size, tiger.tiger(buf).digest()))
                buf = h.read(self.blocksize)
            h.close()
        else:
            # File is empty, special-case hash
            if self.thex:
                leaves = [(0, tiger.tiger("\x00").digest())]
            else:
                leaves = [(0, tiger.tiger("").digest())]

        level = [Branch.as_incomplete(size, hash, is_leaf=True, thex=self.thex)
            for size, hash in leaves]
        self.levels = 0

        # Reduce leaves and branches to get a top node.
        while len(level) > 1:
            self.levels += 1

            # If there's a spare branch on the end, reuse it instead of having
            # to create a new branch just to hold it.
            trailing = level[-1] if len(level) % 2 else None

            level = [Branch(left, right, thex=self.thex)
                for left, right in grouper(2, level)]

            if trailing is not None:
                level.append(trailing)

        self.top = level[0]
        self.complete = True

        self.update_offsets()
