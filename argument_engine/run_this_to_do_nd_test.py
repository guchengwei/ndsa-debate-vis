import unittest
import HtmlTestRunner
from argument_engine.natural_deduction import *


class RulesOfImplicationTest(unittest.TestCase):
    """
    test implication rules
    """
    def test_hypothetical_syllogism(self):
        premise = [If("p", "q"), If("q", "r")]
        conclusion = If("p", "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_constructive_dilemma(self):
        premise = [If("p", "q"), If("r", "s"), Or("p", "r")]
        conclusion = Or("q", "s")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())


class RulesOfReplacementTest(unittest.TestCase):
    """
    test replacement rules
    """
    def test_commutativity1(self):
        premise = [Or("p", "q")]
        conclusion = Or("q", "p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_commutativity2(self):
        premise = [And("p", "q")]
        conclusion = And("q", "p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_associativity1(self):
        premise = [Or("p", Or("q", "r"))]
        conclusion = Or(Or("p", "q"), "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_associativity2(self):
        premise = [And("p", And("q", "r"))]
        conclusion = And(And("p", "q"), "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_distribution1_1(self):
        premise = [And("p", Or("q", "r"))]
        conclusion = Or(And("p", "q"), And("p", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_distribution1_2(self):
        premise = [Or(And("p", "q"), And("p", "r"))]
        conclusion = And("p", Or("q", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_distribution2_1(self):
        premise = [Or("p", And("q", "r"))]
        conclusion = And(Or("p", "q"), Or("p", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_distribution2_2(self):
        premise = [And(Or("p", "q"), Or("p", "r"))]
        conclusion = Or("p", And("q", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_transposition(self):
        premise = [If("p", "q")]
        conclusion = If(Not("q"), Not("p"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_material_implication1(self):
        premise = [If("p", "q")]
        conclusion = Or(Not("p"), "q")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_material_implication2(self):
        premise = [Or(Not("p"), "q")]
        conclusion = If("p", "q")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_exportation1(self):
        premise = [If(And("p", "q"), "r")]
        conclusion = If("p", If("q", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_exportation2(self):
        premise = [If("p", If("q", "r"))]
        conclusion = If(And("p", "q"), "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_tautology1_1(self):
        premise = ["p"]
        conclusion = Or("p", "p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_tautology1_2(self):
        premise = [Or("p", "p")]
        conclusion = "p"
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_tautology2_1(self):
        premise = ["p"]
        conclusion = And("p", "p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test_tautology2_2(self):
        premise = [And("p", "p")]
        conclusion = "p"
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())


class ConditionalProofTest(unittest.TestCase):
    """
    test conditional proof
    """
    def test1_1(self):
        premise = [If(Or("p", "q"), "r")]
        conclusion = And(If("p", "r"), If("q", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test1_2(self):
        premise = [And(If("p", "r"), If("q", "r"))]
        conclusion = If(Or("p", "q"), "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test2_1(self):
        premise = [If("p", "q"), If("p", "r")]
        conclusion = If("p", And("q", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test2_2(self):
        premise = [If("p", And("q", "r"))]
        conclusion = And(If("p", "q"), If("p", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test3(self):
        premise = [If("a", "b")]
        conclusion = If(If("b", "c"), If("a", "c"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test4(self):
        premise = [If("p", If("q", "r")), If("p", If("s", Not("t"))), If("t", Or("q", "s"))]
        conclusion = If("p", If("t", "r"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test5(self):
        premise = [If("p", If(Or("q", "r"), And("s", "t"))), If(Or("t", "u"), "w")]
        conclusion = If("p", If("r", "w"))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test6(self):
        premise = [If("p", If(Or("q", Not("q")), Or("r", "s"))), If("s", Not(Or("t", Not("t"))))]
        conclusion = If("p", "r")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())


class IndirectProofTest(unittest.TestCase):
    """
    test indirect proof
    """
    def test1(self):
        premise = [And("p", Not("q"))]
        conclusion = And("p", Not(If("p", "q")))
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test2(self):
        premise = [If(Or("p", "q"), Not("p"))]
        conclusion = Not("p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test3(self):
        premise = [If(If("p", "p"), "q"), If(Or("q", 'r'), "s")]
        conclusion = "s"
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test4(self):
        premise = [If(Or("p", "q"), And("r", "s")),
                   If(Or("s", "t"), Or("u", Not("r"))),
                   If(Or("u", "w"), Not(And("p", "s")))]
        conclusion = Not("p")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test5(self):
        premise = [Or(And("p", "q"), And("r", "s")), If(Or("q", "r"), Not("s"))]
        conclusion = "q"
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())

    def test6(self):
        premise = [Or("q", If("r", "s")),
                   If(If("r", If("r", "s")), Or("t", "u")),
                   And(If("t", "q"), If("u", "v"))]
        conclusion = Or("q", "v")
        self.assertTrue(NaturalDeduction(premise, conclusion).prove())


if __name__ == '__main__':
    # unittest.main()
    suite1 = unittest.TestLoader().loadTestsFromTestCase(RulesOfImplicationTest)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(RulesOfReplacementTest)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(ConditionalProofTest)
    suite4 = unittest.TestLoader().loadTestsFromTestCase(IndirectProofTest)

    suite = unittest.TestSuite([suite1, suite2, suite3, suite4])

    h = HtmlTestRunner.HTMLTestRunner(report_name="NDTestReport", report_title="Natural Deduction Unittest Results",
                                      template='template0.html', combine_reports=True, open_in_browser=True).run(suite)
