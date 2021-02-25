import copy
from argument_engine.nd_rules import *

'''Lookups '''


def pre_lookup(init_premise, count, conclu=None, assume=None):
    """
    search in premises to see if rules can be applied
    """
    new_pre = init_premise.copy()
    counter = count
    index = len(init_premise) - 1
    while index >= 0:
        if assume:
            prop, counter = Checks(init_premise[index], index, new_pre, counter, assume=assume).bottom_check()
            # within ifi proof or raa proof, check if contradiction exists
            if prop == 'bottom':
                return 'bottom', counter
        if conclu:
            prop, counter = conclu_lookup(conclu, new_pre, counter, assume=assume)
            # within ifi proof, a quick check of current conclusion. ex.p>q when assume p, check if q meets.

            if prop is True:  # meaning the whole formula is solved. (this maybe useless)
                return True, counter
            elif prop == 'bottom':  # meaning find contradiction
                return 'bottom', counter
            elif prop is not None:  # meaning current conclusion meets
                return prop, counter

        generator = Checks(init_premise[index], index, new_pre, counter, assume=assume).check()
        # enter general check procedure
        for x in generator:
            p, counter = x
            if p:
                for item in p:
                    new_pre.append(item)
                break

        if new_pre != init_premise:  # find something
            new_pre, counter = pre_lookup(new_pre, counter, assume=assume)  # enter a new round of lookup
            if new_pre == 'bottom':
                return 'bottom', counter
            elif new_pre is True:
                return True, counter

        index -= 1

    return new_pre, counter


def conclusion_lookup(pre_list, con_list, count, assume=None):
    """
    search in conclusion to see if any rules can be applied
    comment-x:2020-Nov-10

    Args:
        pre_list: premises(all clauses we can use right now) in a list
        con_list: conclusion in a list
        count: how many lines do we have.
        assume: If it is in a conditional proof.

    Returns:
        pre: (new) premises(all clauses we can use right now) in a list
        counter: (new) how many lines do we have .
    """

    pre = pre_list.copy()
    con = con_list.copy()
    counter = count
    ele = 0
    while True:
        if ele >= len(con):
            break
        new_pre = pre.copy()
        new_con = con.copy()
        if duplicates(con[ele], pre):  # check if a clause in the conclusion list exits
            if ele == 0:  # is it the goal?
                if not assume:  # yes
                    return True, counter
                else:  # just a subgoal
                    return con[ele], counter
            else:
                new_con.remove(con[ele])
        else:
            generator = Checks(con[ele], ele, pre, counter, direction=1, assume=assume).check()
            for x in generator:
                p, counter = x
                if p:
                    for item in p:
                        new_pre.append(item)
                    break
        if new_pre != pre:  # find something in check procedure, loop from beginning
            pre = new_pre
            ele = 0
        elif new_con != con:  # a clause in conclusion is meet and deleted
            con = new_con
            continue
        else:
            ele += 1

    if assume:
        return pre, counter

    else:
        if isinstance(con[0], Not) or isinstance(con[0], Atom) or isinstance(con[0], Or):
            # nothing above works, try raa
            prop, counter = raa(pre, con[0], counter, assume=assume)
            for item in prop:
                pre.append(item)

            return conclusion_lookup(pre, con, counter, assume=assume)

        # elif isinstance(con[0], If):
        #     # nothing above works, try ifi (probably useless)
        #     prop, counter = if_i(con[0], pre, con, counter, assume=assume)
        #     for item in prop:
        #         pre.append(item)
        #     return conclusion_lookup(pre, con, counter, assume=assume)

        else:  # nothing above works, try assume or
            ele = 0
            while ele <= len(pre) - 1:
                if isinstance(pre[ele], Or) and not pre[ele].created:
                    prop, counter = assume_or(pre[ele], pre, con, counter, assume=assume)
                    for item in prop:
                        pre.append(item)
                    return conclusion_lookup(pre, con, counter, assume=assume)
                ele += 1

        exit(" can't solve error")  # we are done for


def conclu_lookup(conclu, pre_list, counter, assume=None):
    """
    a quick check of the current conclusion, no recursion
    """
    generator = Checks(conclu, -1, pre_list, counter, direction=1, assume=assume).check()
    for x in generator:
        p, counter = x
        if p:
            return p, counter
    return None, counter


'''Checks'''


class Checks:

    def __init__(self, arg, index, premises, count, direction=None, assume=None):
        self.arg = arg
        self.index = index
        self.premises = premises
        self.count = count
        self.direction = direction
        self.assume = assume

    def check(self):
        """
        direction=None, premise lookup. direction=1, conclusion lookup.
        """
        yield self.and_check()

        yield self.or_check()

        yield self.not_check()

        yield self.modus_check()

        yield self.if_check()

    def and_check(self):
        """
        check AndI, AndE
        """
        if not isinstance(self.arg, And):
            return None, self.count

        if self.direction:
            assert0 = duplicates(self.arg.args[0], self.premises)
            assert1 = duplicates(self.arg.args[1], self.premises)
            if assert0 and assert1:
                new_p, self.count = and_i(self.arg.args[0], self.arg.args[1],
                                          int(assert0), int(assert1), self.count, assume=self.assume)
                new_p.created = True
                return [new_p], self.count

        elif not self.arg.created:
            new_p, self.count = and_e(self.arg, self.index, self.count, assume=self.assume)
            self.arg.created = True
            return new_p, self.count

        return None, self.count

    def or_check(self):
        """
         check OrI, mtp( w/o dm)
        """
        if self.direction:
            if isinstance(self.arg, Or):
                assert0 = duplicates(self.arg.args[0], self.premises)
                assert1 = duplicates(self.arg.args[1], self.premises)
                if assert0 or assert1:
                    position = int(assert0 if assert0 else assert1)
                    new_p, self.count = or_i(self.arg.args[0], self.arg.args[1],
                                             position, self.count, assume=self.assume)
                    new_p.created = True
                    return [new_p], self.count

        else:
            prop = self.arg.args[0] if isinstance(self.arg, Not) else Not(self.arg)

            for ele in range(0, len(self.premises)):
                if isinstance(self.premises[ele], Or) and not self.premises[ele].created:
                    if duplicates(prop, self.premises[ele].args[0]) or duplicates(prop, self.premises[ele].args[1]):
                        new_p, self.count = modus_tollendo_ponens(self.arg, self.premises[ele],
                                                                  self.index, ele, self.count, assume=self.assume)
                        self.premises[ele].created = True
                        return [new_p], self.count

        return None, self.count

    def not_check(self):
        """
        check dn, dm(~(p|q) -> ~p&~q)
        """
        if not isinstance(self.arg, Not):
            return None, self.count

        if self.direction:
            assert0 = duplicates(self.arg.args[0].args[0], self.premises)
            if isinstance(self.arg.args[0], Not) and assert0:
                new_p, self.count = double_negation(self.arg.args[0], int(assert0),
                                                    self.count, direction=1, assume=self.assume)
                new_p.created = True
                return [new_p], self.count
            elif not isinstance(self.arg.args[0], Atom):
                new_p, self.count = raa(self.premises, self.arg, self.count, assume=self.assume)
                return new_p, self.count

        elif not self.arg.created:
            if isinstance(self.arg.args[0], Not):
                new_p, self.count = double_negation(self.arg, self.index, self.count, assume=self.assume)
                self.arg.created = True
                return [new_p], self.count

            elif not isinstance(self.arg.args[0], Atom):
                new_p, self.count = de_morgan(self.arg, self.index, self.count, assume=self.assume)
                self.arg.created = True
                return [new_p], self.count

        return None, self.count

    def modus_check(self):
        """
        check dm, mt, mtp
        """
        prop, self.count = self.check_dm()

        if prop is None:
            prop, self.count = self.check_if_or()

        if prop is None:
            return None, self.count
        else:
            return prop, self.count

    def check_dm(self):
        """
        check dm(~p&~q -> ~(p|q))
        """
        if self.direction:
            if isinstance(self.arg, Not):
                if isinstance(self.arg.args[0], And) or isinstance(self.arg.args[0], Or):
                    prop1 = self.arg.args[0].args[0].args[0] \
                        if isinstance(self.arg.args[0].args[0], Not) else Not(self.arg.args[0].args[0])
                    prop2 = self.arg.args[0].args[0].args[1] \
                        if isinstance(self.arg.args[0].args[1], Not) else Not(self.arg.args[0].args[1])
                    assert1 = duplicates(prop1, self.premises)
                    assert2 = duplicates(prop2, self.premises)
                    new_prop1 = None
                    if isinstance(self.arg.args[0], And):
                        if assert1:
                            new_prop1, self.count = or_i(prop1, prop2, int(assert1), self.count, assume=self.assume)
                        elif assert2:
                            new_prop1, self.count = or_i(prop1, prop2, int(assert1), self.count, assume=self.assume)

                    elif isinstance(self.arg.args[0], Or):
                        if assert1 and assert2:
                            new_prop1, self.count = and_i(prop1, prop2, int(assert1),
                                                          int(assert2), self.count, assume=self.assume)

                    if new_prop1:
                        new_prop2, self.count = de_morgan(new_prop1, self.count - 1, self.count, direction=1,
                                                          assume=self.assume)
                        new_prop1.created = True
                        new_prop2.created = True
                        return [new_prop1, new_prop2], self.count

        else:
            pre_list = listlize(self.premises, "DM")
            prop = self.arg.args[0] if isinstance(self.arg, Not) else Not(self.arg)
            new_prop1 = None
            for ele in pre_list:
                assert0 = duplicates(prop, ele.args)
                if not assert0:
                    continue

                if isinstance(ele, And):
                    if int(assert0) == 0:
                        new_prop1, self.count = or_i(self.arg, Not(ele.args[1]),
                                                     self.index, self.count, assume=self.assume) \
                            if not isinstance(ele.args[1], Not) else or_i(self.arg, ele.args[1].args[0],
                                                                          self.index, self.count, assume=self.assume)

                    else:
                        new_prop1, self.count = or_i(Not(ele.args[0]), self.arg,
                                                     self.index, self.count, assume=self.assume) \
                            if not isinstance(ele.args[0], Not) else or_i(ele.args[0].args[0], self.arg,
                                                                          self.index, self.count, assume=self.assume)

                elif isinstance(ele, Or):
                    if int(assert0) == 0:
                        assert1 = duplicates(Not(ele.args[1]), self.premises)
                        assert2 = duplicates(ele.args[1].args[0], self.premises)

                        if not isinstance(ele.args[1], Not) and assert1:
                            new_prop1, self.count = and_i(self.arg, Not(ele.args[1]),
                                                          self.index, int(assert1), self.count, assume=self.assume)
                        elif isinstance(ele.args[1], Not) and assert2:
                            new_prop1, self.count = and_i(self.arg, ele.args[1].args[0],
                                                          self.index, int(assert2), self.count, assume=self.assume)

                    else:
                        assert1 = duplicates(Not(ele.args[0]), self.premises)
                        assert2 = duplicates(ele.args[0].args[0], self.premises)
                        if not isinstance(ele.args[0], Not) and assert1:
                            new_prop1, self.count = and_i(Not(ele.args[0]), self.arg,
                                                          int(assert1), self.index, self.count, assume=self.assume)
                        elif isinstance(ele.args[0], Not) and assert2:
                            new_prop1, self.count = and_i(ele.args[0].args[0], self.arg,
                                                          int(assert2), self.index, self.count, assume=self.assume)

                if new_prop1:
                    new_prop2, self.count = de_morgan(new_prop1, self.count - 1, self.count,
                                                      direction=1, assume=self.assume)
                    new_prop1.created = True
                    new_prop2.created = True
                    return [new_prop1, new_prop2], self.count

        return None, self.count

    def check_if_or(self):
        """
        check hidden and, or
        """
        pre_list = listlize(self.premises, "IF,OR")
        new_prop = None
        for ele in pre_list:
            assert0 = duplicates(self.arg, ele.args)
            if not assert0:
                continue

            if isinstance(ele, And) and not ele.created:
                if int(assert0) == 0:
                    assert1 = duplicates(ele.args[1], self.premises)
                    if assert1:
                        new_prop, self.count = and_i(self.arg, ele.args[1],
                                                     self.index, int(assert1), self.count, assume=self.assume)
                else:
                    assert1 = duplicates(ele.args[0], self.premises)
                    if assert1:
                        new_prop, self.count = and_i(ele.args[0], self.arg,
                                                     int(assert1), self.index, self.count, assume=self.assume)

            elif isinstance(ele, Or) and not ele.created:
                if int(assert0) == 0:
                    new_prop, self.count = or_i(self.arg, ele.args[1], self.index, self.count, assume=self.assume)
                else:
                    new_prop, self.count = or_i(ele.args[0], self.arg, self.index, self.count, assume=self.assume)

            if new_prop:
                ele.created = True
                new_prop.created = True
                return [new_prop], self.count

        return None, self.count

    def bottom_check(self):
        """
        check contradiction
        """
        if isinstance(self.arg, And) and (
                duplicates(Not(self.arg.args[0]), self.arg.args[1]) or
                duplicates(self.arg.args[0], Not(self.arg.args[1]))):
            result, self.count = bottom(self.arg, None, self.index, -1, self.count, assume=self.assume)
        else:
            assert0 = duplicates(self.arg.args[0], self.premises)
            assert1 = duplicates(Not(self.arg), self.premises)
            result = None

            if isinstance(self.arg, Not) and assert0:
                result, self.count = bottom(self.arg, self.arg.args[0],
                                            self.index, int(assert0), self.count, assume=self.assume)
            elif not isinstance(self.arg, Not) and assert1:
                result, self.count = bottom(self.arg, Not(self.arg),
                                            self.index, int(assert1), self.count, assume=self.assume)

        if result == 'bottom':
            return 'bottom', self.count
        else:
            return None, self.count

    def if_check(self):
        """
         check IfI, IfE, mt( w/o dm)
        """
        if self.direction:
            if isinstance(self.arg, If) and not self.assume:
                prop, self.count = if_i(self.arg, self.premises, listlize([self.arg], "CON"), self.count)
                return prop, self.count

        else:

            for ele in range(0, len(self.premises)):

                if isinstance(self.premises[ele], If) and not self.premises[ele].created:
                    if duplicates(self.arg, self.premises[ele].args[0]):
                        new_p, self.count = if_e(self.premises[ele], self.index, ele, self.count, assume=self.assume)
                        self.premises[ele].created = True
                        return [new_p], self.count

                    else:
                        prop = self.premises[ele].args[1].args[0] \
                            if isinstance(self.premises[ele].args[1], Not) else Not(self.premises[ele].args[1])

                        if duplicates(self.arg, prop):
                            new_p, self.count = modus_tollens(self.premises[ele], self.index, ele,
                                                              self.count, assume=self.assume)
                            self.premises[ele].created = True
                            return [new_p], self.count

        return None, self.count


'''RAA'''


def raa(raa_premise, raa_conclusion, count, assume=None):
    """
    prove by contradiction procedure
    """
    r_premise = copy.deepcopy(raa_premise)
    if not assume:
        assume = 1
    else:
        assume += 1

    print_prefix(count, assume)
    print(f"| RAA Assume {Not(raa_conclusion)}")

    r_premise.append(Not(raa_conclusion))
    count += 1
    result, n_count = pre_lookup(r_premise, count, assume=assume)
    if result == 'bottom':
        prop = [Atom("0")] * (n_count - count + 1)  # keep the length of premises
        prop.append(raa_conclusion)
        assume -= 1

        print_prefix(n_count, assume)
        print(f"| Therefore {raa_conclusion} -- {n_count - 1}")

        n_count += 1
        return prop, n_count
    else:
        raise Exception("raa error")


'''IfI'''


def if_i(if_formula, if_premise, if_conclusion, count, assume=None):
    """
    conditional proof prepossessing, make a candidate list
    """
    promises = copy.deepcopy(if_premise)
    candidate = listlize(if_premise, "IFI", args2=if_formula)
    prop, n_count = conditional_proof(candidate, 0, promises, if_conclusion, count, assume=assume)
    if duplicates(prop, if_formula):
        prop = [Atom("0")] * (n_count - count - 1)  # keep the length of premises
        prop.append(if_formula)
        return prop, n_count
    else:
        raise Exception("Ifi error")


def conditional_proof(candidate_list, index, pre, conclusions, count, assume=None):
    """
    conditional proof procedure
    """
    premises = pre.copy()
    current_conclusion = None
    for ele in conclusions:
        if isinstance(ele, If) and duplicates(candidate_list[index], ele.args[0]):
            current_conclusion = ele.args[1]

    if not assume:
        assume = 1
    else:
        assume += 1

    print_prefix(count, assume)
    print(f"| IfI Assume {candidate_list[index]}")

    position1 = count
    count += 1
    n_count = None

    premises.append(candidate_list[index])

    while True:
        old_premises = premises
        if n_count:  # meaning has gone through the recursion part
            while len(premises) < n_count - 1:
                premises[(count - 1):(count - 1)] = [Atom("0")]  # keep the length of premises
            premises, count = pre_lookup(premises, n_count, conclu=current_conclusion, assume=assume)
        else:
            premises, count = pre_lookup(premises, count, conclu=current_conclusion, assume=assume)

        if premises == 'bottom':  # find contradiction

            if current_conclusion:
                prop = current_conclusion
                while len(old_premises) < count - 1:
                    old_premises[(count - 1):(count - 1)] = [Atom("0")]
                old_premises.append(prop)
                premises = old_premises
            else:
                assume -= 1
                prop = candidate_list[index].args[0] \
                    if isinstance(candidate_list[index], Not) else Not(candidate_list[index])

            print_prefix(count, assume)
            print(f"| Therefore {prop} -- {count - 1}")
            count += 1

            if not current_conclusion:
                return prop, count

        elif premises is True:  # the goal is meet
            return True, count
        else:
            if current_conclusion is None and (n_count or index == len(candidate_list) - 1):
                # no q, can't form a p>q, try raa p
                prop1 = If(candidate_list[index], premises[-1])
                assume -= 1

                print_prefix(count, assume)
                print(f"| Therefore,{prop1} --IfI {position1},{len(premises)}")

                count += 1
                premises.append(prop1)
                for i in range(position1 - 1, len(premises) - 1):  # cover the premises that can't use
                    premises[i] = Atom("0")
                prop2, n_count = raa(premises, candidate_list[index], count, assume=assume)

                if duplicates(candidate_list[index], prop2):
                    return [prop1] + prop2, n_count
                else:
                    exit("Ifi raa error")

            elif isinstance(candidate_list[index], Or):
                assert1 = duplicates(candidate_list[index].args[0], candidate_list)
                assert2 = duplicates(candidate_list[index].args[1], candidate_list)
                if assert1 and assert2:
                    # can't deal with p|q, try assume or
                    prop, count = assume_or(candidate_list[index], premises,
                                            [current_conclusion], count, assume=assume)
                    if int(assert1) > int(assert2):
                        candidate_list.pop(int(assert1))
                        candidate_list.pop(int(assert2))
                    else:
                        candidate_list.pop(int(assert2))
                        candidate_list.pop(int(assert1))
                    if duplicates(current_conclusion, prop):
                        premises = premises + prop
                    else:
                        raise Exception("Ifi or assume error")

        position2 = duplicates(current_conclusion, premises)
        if position2:  # p>q can be formed
            prop = If(candidate_list[index], current_conclusion)
            assume -= 1

            print_prefix(count, assume)
            print(f"| Therefore {prop} --IfI {position1},{int(position2) + 1}")

            count += 1
            return prop, count

        index += 1
        if len(candidate_list) == index:
            raise Exception("Ifi index error")
        else:
            prop, n_count = conditional_proof(candidate_list, index, premises,
                                              conclusions, count, assume=assume)  # try next candidate
            candidate_list.pop(index)
            index -= 1

            if isinstance(prop, list):
                for i in prop:
                    premises.append(i)
            else:
                premises.append(prop)


'''Or Assume'''


def assume_or(or_formula, or_premise, or_conclusion, count, assume=None):
    """
    deal with p|q
    """
    if not assume:
        assume = 1
    else:
        assume += 1
    init_count = count
    n_count = None
    index_list = []
    for prop in or_formula.args:
        premises = copy.deepcopy(or_premise)
        if n_count:
            while len(premises) < n_count - 1:  # keep the length of premises
                premises.append(Atom("0"))

        print_prefix(count, assume)
        print(f"| Or Assume {prop}")

        count += 1
        premises.append(prop)
        premises, count = pre_lookup(premises, count, assume=assume)
        result, n_count = conclusion_lookup(premises, or_conclusion, count, assume=assume)
        if duplicates(result, or_conclusion[0]):
            count = n_count
            index_list.append(n_count - 1)
        elif isinstance(prop, Or):
            result, n_count = assume_or(prop, result, or_conclusion, n_count, assume=assume)
            index_list.append(n_count - 1)
        else:
            raise Exception("assume or error")

    prop = [Atom("0")] * (count - init_count)  # keep the length of premises
    prop.append(or_conclusion[0])
    assume -= 1

    print_prefix(n_count, assume)
    print(f"| Therefore {or_conclusion[0]} -- {index_list[0]}, {index_list[1]}")

    count += 1
    return prop, count
