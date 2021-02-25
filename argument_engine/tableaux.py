from argument_engine.nd_formula import Formula, Atom, If, And, Or, Not, SymbolToFunction, duplicates


class TableauxProve:

    def __init__(self, clause, init=None, show_proof=False):
        self.clause = clause
        self.show_proof = show_proof
        if init == 'first-run':  # first run
            self.clause[0].sign = "F"
        elif init == 'consistency':  # try to figure out whether the premise is inconsistent
            self.clause[0].sign = "T"

    def search(self):
        """
        Tableaux proof procedure
        """
        if self.show_proof:
            for item in self.clause:
                if item.branch:
                    for i in range(item.branch):
                        print("|", end="")
            print(", ".join(map(str, self.clause)))

        if self.is_closed():  # check if the clause set is closed
            if self.show_proof:
                for item in self.clause:
                    if item.branch:
                        for i in range(item.branch):
                            print("|", end="")
                print("closed")
            return True

        candidate_clause = self.slim()

        if not candidate_clause:
            if self.show_proof:
                for item in self.clause:
                    if item.branch:
                        for i in range(item.branch):
                            print("|", end="")
                print("Can't be closed")
            return False

        for item in candidate_clause:
            generator = item.solve()
            clauses = self.clause.copy()
            clauses.remove(item)
            for new in generator:
                if not TableauxProve(clauses + new, show_proof=self.show_proof).search():
                    return False  # one branch can't be closed
            return True  # all branches closed

    def slim(self):
        """
        remove duplicates and literals
        """
        new = []
        for item in self.clause:
            if isinstance(item, Atom):
                continue
            elif duplicates(item, new):
                continue
            else:
                new.append(item)
        return new

    def is_closed(self):
        """
        check if two clause contradicts
        """
        for item in self.clause:
            clauses = self.clause.copy()
            clauses.remove(item)
            for another in clauses:
                if item.closed(another):
                    return True
        return False


class Tableaux:

    def __init__(self, conclusion_is_a_formula, premise_in_a_list=None, show_proof=False):
        if isinstance(conclusion_is_a_formula, Formula):
            self.conclusion = conclusion_is_a_formula
        else:
            self.conclusion = SymbolToFunction(conclusion_is_a_formula).transform()

        if premise_in_a_list and not any(isinstance(item, Formula) for item in premise_in_a_list):
            self.premise = [SymbolToFunction(pre).transform() for pre in premise_in_a_list]
        else:
            self.premise = premise_in_a_list

        self.show_proof = show_proof

    def prove(self, consistency_test=None):
        """
        handle situation w/ or w/o premise
        """
        if self.premise:
            pre = self.prepossessing()
            if consistency_test:  # try to figure out whether the premise set is inconsistent
                if TableauxProve([pre], init='consistency').search():
                    return False
            clause = If(pre, self.conclusion)
        else:
            clause = self.conclusion

        if TableauxProve([clause], init='first-run', show_proof=self.show_proof).search():
            result = True
        else:
            result = False

        if self.premise:
            for item in self.premise:
                item.sign = None
        self.conclusion.sign = None

        if self.show_proof:
            if self.premise:
                print(", ".join(map(str, self.premise)), end=" ")
            print("|- " if result else "|\\- ", end="")
            print(self.conclusion)

        return True if result else False

    def prepossessing(self):
        """
        combine premise and conclusion into a single clause
        """
        number_of_premises = len(self.premise)
        if number_of_premises == 1:
            premises = self.premise[0]
        elif number_of_premises == 2:
            premises = And(self.premise[0], self.premise[1])
        else:
            premises = And(self.premise[0], self.premise[1])
            for index in range(2, number_of_premises):
                premises = And(premises, self.premise[index])

        return premises


# if __name__ == "__main__":
    # Tableaux(If(If("A", "B"), If(If("B", "C"), If("A", "C"))), show_proof=True).prove()
    #
    # Tableaux(And("A", Not("A")), show_proof=True).prove()

    # premise = [If("p", If("q", "r")), If("p", If("s", Not("t"))), If("t", Or("q", "s"))]
    # conclusion = If("p", If("t", "r"))

    # premise = ["p>(q>r)", "p>(s>~t)", "t>(q|s)"]
    # conclusion = "p>(t>r)"
    # Tableaux(conclusion, premise_in_a_list=premise, show_proof=True).prove()


