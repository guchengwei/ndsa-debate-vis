class Formula:
    """
    structure used to store formula
    """

    def __init__(self, sign=None, branch=None):
        self.symbol = None
        self.args = None
        self.created = None
        """
        if created is true , it means that the clause which can be decomposed 
        has already introduced or been introduced by another clause, it won't be checked again. 
        """
        self.sign = sign
        self.branch = branch

    def __str__(self):
        sign = self.sign if self.sign else ""
        return sign + self.func_to_sym()

    def func_to_sym(self):
        """
        input: Or("p","q") output: p|q
        """
        if len(self.args) > 1 and self.symbol:
            return ("({})".format(self.args[0].func_to_sym())
                    if len(self.args[0].args) > 1 else "{}".format(self.args[0].func_to_sym())) + \
                   self.symbol + \
                   ("({})".format(self.args[1].func_to_sym())
                    if len(self.args[1].args) > 1 else "{}".format(self.args[1].func_to_sym()))
        elif self.symbol:
            return self.symbol + \
                   ("({})".format(self.args[0].func_to_sym())
                    if self.args[0].symbol else "{}".format(self.args[0].func_to_sym()))
        else:
            return self.args

    def closed(self, another):
        return self.args == another.args and self.sign and another.sign and self.sign != another.sign


class Atom(Formula):
    """
    store atom formula
    """

    def __init__(self, args):
        super().__init__()
        self.symbol = ""
        self.args = args


class And(Formula):
    """
    store and formula
    """

    def __init__(self, *args):
        super().__init__()
        self.symbol = "&"
        self.args = [Atom(item) if isinstance(item, str) else item for item in args]

    def solve(self):
        arg1, arg2 = self.args
        arg1.sign = self.sign
        arg2.sign = self.sign
        arg1.branch = self.branch
        arg2.branch = self.branch
        if self.sign == "T":
            yield [arg1, arg2]
        elif self.sign == "F":
            if self.branch:
                arg1.branch += 1
                arg2.branch += 1
            else:
                arg1.branch = 1
                arg2.branch = 1
            yield [arg1]
            yield [arg2]


class Or(Formula):
    """
    store or formula
    """

    def __init__(self, *args):
        super().__init__()
        self.symbol = "|"
        self.args = [Atom(item) if isinstance(item, str) else item for item in args]

    def solve(self):
        arg1, arg2 = self.args
        arg1.sign = self.sign
        arg2.sign = self.sign
        arg1.branch = self.branch
        arg2.branch = self.branch
        if self.sign == "T":
            if self.branch:
                arg1.branch += 1
                arg2.branch += 1
            else:
                arg1.branch = 1
                arg2.branch = 1
            yield [arg1]
            yield [arg2]
        elif self.sign == "F":
            yield [arg1, arg2]


class Not(Formula):
    """
    store not formula
    """

    def __init__(self, *args):
        super().__init__()
        self.symbol = "~"
        self.args = [Atom(item) if isinstance(item, str) else item for item in args]

    def solve(self):
        arg = self.args[0]
        arg.sign = "T" if self.sign == "F" else "F"
        arg.branch = self.branch
        yield [arg]


class If(Formula):
    """
    store if formula
    """

    def __init__(self, *args):
        super().__init__()
        self.symbol = ">"
        self.args = [Atom(item) if isinstance(item, str) else item for item in args]

    def solve(self):
        arg1, arg2 = self.args
        arg1.branch = self.branch
        arg2.branch = self.branch
        if self.sign == "T":
            arg1.sign = "F"
            arg2.sign = "T"
            if self.branch:
                arg1.branch += 1
                arg2.branch += 1
            else:
                arg1.branch = 1
                arg2.branch = 1
            yield [arg1]
            yield [arg2]
        elif self.sign == "F":
            arg1.sign = "T"
            arg2.sign = "F"
            yield [arg1, arg2]


class SymbolToFunction:

    def __init__(self, clause):
        self.clause = clause

    dict1 = {
        "&": And,
        "|": Or,
        ">": If
    }

    dict2 = {
        "~": Not
    }

    def bracket_match(self):
        """
        not intend to examine whether the clause is legal. return the position where "(" and ")" matches.
        """
        bracket = 0
        for index in range(0, len(self.clause)):
            if self.clause[index] == "(":
                bracket += 1
            elif self.clause[index] == ")":
                bracket -= 1
            if bracket == 0 and self.clause[index] in self.dict1:
                return index
        return len(self.clause) - 1

    def bracket_strip(self):
        """
        remove useless brackets
        """
        if self.clause[0] == "(" and self.clause[-1] == ")" \
                and self.bracket_match() == len(self.clause) - 1:
            return self.clause[1:-1]
        return self.clause

    def transform(self):
        """
        input "p>q" output: If("p","q")
        """
        new_cla = self.bracket_strip()
        if len(new_cla) <= 2:
            if "~" in new_cla:
                return self.dict2['~'](new_cla[1:])
            else:
                return Atom(new_cla)

        if new_cla[0:2] == "~(" and SymbolToFunction(new_cla[1:]).bracket_match() == len(new_cla[1:]) - 1:
            return self.dict2["~"](SymbolToFunction(new_cla[2:-1]).transform())

        position = SymbolToFunction(new_cla).bracket_match()
        return self.dict1[new_cla[position]](SymbolToFunction(new_cla[0:position]).transform(),
                                             SymbolToFunction(new_cla[position + 1:]).transform())


def duplicates(clause, clause_list):
    """
    find out if a clause in a clause list. if true, return position, else return false
    """
    if not isinstance(clause_list, list):
        if str(clause) == str(clause_list):
            return True
    else:
        for cla in range(0, len(clause_list)):
            if str(clause) == str(clause_list[cla]):
                return str(cla)
    return False


def listlize(args, type_code, args2=None):
    """
    make a candidate list for different purpose
    """
    lookup_list = []
    if type_code == "DM":  # for de morgan's law check

        for it in args:
            if isinstance(it, Or):
                for items in it.args:
                    if not isinstance(items, Not):
                        lookup_list.append(items)

            elif isinstance(it, If):
                if isinstance(it.args[0], Not):
                    lookup_list.append(it.args[0].args[0])
                if not isinstance(it.args[1], Not):
                    lookup_list.append(it.args[1])

    elif type_code == "IF,OR":  # for modus tollens, modus tollendo ponens check

        for it in args:
            if isinstance(it, If):
                if not isinstance(it.args[0], Not):
                    lookup_list.append(it.args[0])
                if isinstance(it.args[1], Not):
                    lookup_list.append(it.args[1].args[0])
            elif isinstance(it, Or):
                for items in it.args:
                    if isinstance(items, Not):
                        lookup_list.append(items.args[0])

    elif type_code == "CON":  # for conclusion lookup

        for it in args:
            lookup_list.append(it) if not isinstance(it, str) else lookup_list.append(Atom(it))
        start = 0
        while True:
            if start == len(lookup_list):
                break
            shift = len(lookup_list)
            for it in range(start, len(lookup_list)):
                if isinstance(lookup_list[it], Atom) or isinstance(lookup_list[it], Not):
                    continue
                else:
                    assert0 = (not isinstance(lookup_list[it].args[0], Atom) and
                               not (isinstance(lookup_list[it].args[0], Not) and
                                    isinstance(lookup_list[it].args[0].args[0], Atom)))
                    assert1 = (not isinstance(lookup_list[it].args[1], Atom) and
                               not (isinstance(lookup_list[it].args[1], Not) and
                                    isinstance(lookup_list[it].args[1].args[0], Atom)))
                    if assert0:
                        lookup_list.append(lookup_list[it].args[0])
                    if assert1:
                        lookup_list.append(lookup_list[it].args[1])

            start = shift

    elif type_code == "IFI":  # for ifi proof
        for it in args:
            if isinstance(it, If) and not it.created:
                lookup_list.append(it)
        shift = len(lookup_list)
        prop = args2
        while isinstance(prop, If):
            lookup_list.append(prop.args[0])
            prop = prop.args[1]

        start = 0
        changed = False
        while 1:
            new_start = len(lookup_list)
            for it in range(start, len(lookup_list)):
                if isinstance(lookup_list[it], If):
                    changed = True
                    lookup_list.append(lookup_list[it].args[0])
                    if isinstance(lookup_list[it].args[1], If):
                        prop = lookup_list[it].args[1]
                        while isinstance(prop, If):
                            lookup_list.append(prop.args[0])
                            prop = prop.args[1]
            if changed:
                changed = False
                start = new_start
            else:
                break

        alist = []
        for ele in range(0, len(lookup_list)):
            if ele <= shift:
                alist.append(lookup_list[ele])
            elif not duplicates(alist[-1], lookup_list[ele]):
                alist.append(lookup_list[ele])

        lookup_list = alist

        return lookup_list[shift:]

    return lookup_list


# if __name__ == '__main__':
#     a = SymbolToFunction("~a|~b").transform()
#     print(type(a))
