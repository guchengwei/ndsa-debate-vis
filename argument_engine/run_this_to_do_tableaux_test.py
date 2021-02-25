import unittest
import HtmlTestRunner
from argument_engine.tableaux import *


class TestWithoutPremise(unittest.TestCase):
    def setUp(self):
        self.show_proof = True

    def test1(self):
        conclusion = If(If("p", "q"), If(If("q", "r"), If("p", "r")))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test2(self):
        conclusion = If(And(Or("p", "q"), And(If("p", "r"), And(Not("p"), If("q", "r")))), "r")
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test3(self):
        conclusion = If(If(If(If(If("p", "q"), "p"), "p"), "q"), "q")
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test4(self):
        conclusion = Or("p", Not("p"))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test5(self):
        conclusion = Not(Not(Or("p", Not("p"))))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test6(self):
        conclusion = Not(And("p", Not("p")))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test7(self):
        conclusion = If(If(Or("p", Not("p")), "q"), Not(Not("q")))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test8(self):
        conclusion = If("p", Not(Not("p")))
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test9(self):
        conclusion = If(Not(Not("p")), "p")
        self.assertTrue(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test_false1(self):
        conclusion = And("p", Not("p"))
        self.assertFalse(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test_false2(self):
        conclusion = Not(If(Not(Not((Not("p")))), Not("p")))
        self.assertFalse(Tableaux(conclusion, show_proof=self.show_proof).prove())

    def test_false3(self):
        conclusion = If(If("p", "p"), "p")
        self.assertFalse(Tableaux(conclusion, show_proof=self.show_proof).prove())


class TestWithPremise(unittest.TestCase):
    def setUp(self):
        self.show_proof = True

    def test1(self):
        premise = [If("p", If(Or("q", Not("q")), Or("r", "s"))), If("s", Not(Or("t", Not("t"))))]
        conclusion = If("p", "r")
        self.assertTrue(Tableaux(conclusion, premise_in_a_list=premise, show_proof=self.show_proof).prove())

    def test2(self):
        premise = [If("p", If(Or("q", "r"), And("s", "t"))), If(Or("t", "u"), "w")]
        conclusion = If("p", If("r", "w"))
        self.assertTrue(Tableaux(conclusion, premise_in_a_list=premise, show_proof=self.show_proof).prove())

    def test3(self):
        premise = [If("p", If("q", "r")), If("p", If("s", Not("t"))), If("t", Or("q", "s"))]
        conclusion = If("p", If("t", "r"))
        self.assertTrue(Tableaux(conclusion, premise_in_a_list=premise, show_proof=self.show_proof).prove())

    def test_false1(self):
        premise = [If("p", If(Or("q", Not("q")), Or("r", "s"))), If("s", Not(Or("t", Not("t"))))]
        conclusion = Not(If("p", "r"))
        self.assertFalse(Tableaux(conclusion, premise_in_a_list=premise, show_proof=self.show_proof).prove())


if __name__ == '__main__':
    # unittest.main()
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestWithoutPremise)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestWithPremise)

    suite = unittest.TestSuite([suite1, suite2])

    h = HtmlTestRunner.HTMLTestRunner(report_name="TableauxTestReport", report_title="Tableaux Unittest Results",
                                      template='template0.html', combine_reports=True, open_in_browser=True).run(suite)
