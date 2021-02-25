import sys
import io
from argument_engine.nd_lookups import *


class NaturalDeduction:

    # checked-x:2020-Nov-10
    def __init__(self, premise_in_a_list, conclusion_is_a_formula):
        self.premise = premise_in_a_list \
            if any(isinstance(item, Formula) for item in premise_in_a_list) \
            else [SymbolToFunction(pre).transform() for pre in premise_in_a_list]
        self.conclusion = conclusion_is_a_formula \
            if isinstance(conclusion_is_a_formula, Formula) \
            else SymbolToFunction(conclusion_is_a_formula).transform()

    def prove(self):
        """
            Returns:
                result: proof in fitch style.
            """

        # comment-x:2020-Nov-10
        # 1. what are the meanings of old_stdout and new_stdout?    https://docs.python.org/3/library/sys.html
        # can you comment a little bit or rename them to be some meaningful names?  https://docs.python.org/3/library/io.html
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout

        # comment-x:2020-Nov-10
        # 1. what is the meaning of count? does it mean the length of premise_list?     It stands for the number of lines, Including premises and all the proofs.
        # can you comment a little bit or rename them to be some meaningful names?
        # 2. what is the meaning of listlize? does it mean to change an input object into a list?   It generates a list of condidate for different proposes.
        # what is the meaning of CON? Also, [self.conclusion] is already a list? why do we have to listlize?    For example 'Con' stands for conclusion.
        premise_list, count = self.read_premises()
        premise_list, count = pre_lookup(premise_list, count)
        conclusion_list = listlize([self.conclusion], "CON")
        result = conclusion_lookup(premise_list, conclusion_list, count)

        sys.stdout = old_stdout

        if result:
            output = new_stdout.getvalue()
            how_many_lines = output.count('\n')
            if how_many_lines < 10:   # comment-x:2020-Nov-10 why 10 is used?  Counts for lines less than 10 are only 1-digit, this is used for format spacing.
                output = output.replace('. ', '.')

            print(output)
            self.print_result()
            result = output
        else:
            print("Can't prove.")

        return result

    def read_premises(self):
        premises = []
        counter = 1
        for item in self.premise:

            if isinstance(item, str):
                premises.append(Atom(item))
            else:
                premises.append(item)

            print(f"{counter}.", end="")
            print(" " if counter < 10 else "", end="")
            print(f"| Premise {item}")
            counter += 1

        return premises, counter

    def print_result(self):
        print(", ".join(map(str, self.premise)), end=" ")
        print(f"|- {self.conclusion}")






if __name__ == "__main__":

    # test_str1 = "(A>B)>((B>C)>(A>C))"
    # test_str2 = "~(~A|(~A|B))"
    # test_str3 = "~(A|B)&~(B|C)"
    # test_str4 = "~(~(~A))"

    # str_premise = ["p>((q|~q)>(r|s))", "s>~(t|~t)"]
    # str_conclusion = "p>r"
    # premise = ['h', 'r>~h']
    # conclusion = 'r>~a'
    # anlp = NaturalDeduction(premise, conclusion).prove()


    # premise = [If("p", If(Or("q", Not("q")), Or("r", "s"))), If("s", Not(Or("t", Not("t"))))]
    # conclusion = If("p", "r")
    #
    # premise = ['i', 'h>a', 'e>a', 'i>a', 'h', 'l>a', 'e', 'l']
    # conclusion = '~a>~d'
    #
    # premise = ['r', 'h']
    # conclusion = '~(r>~h)'
    #
    # NaturalDeduction(premise, conclusion).prove()
    #
    # premise = [Not(Not(Not(Not("p"))))]
    # conclusion = "p"
    # NaturalDeduction(premise, conclusion).prove()
    #
    # premise = [Or("p", Or("q", "r"))]
    # conclusion = Or(Or("p", "q"), "r")

    # premise = ['p>r', 'p>q']
    # conclusion = 'p>(q&r)'
    # NaturalDeduction(premise,conclusion).prove()

    pass

