from argument_engine.nd_formula import *

'''Basic rules'''


def print_prefix(count, assume):
    print(f"{count}.", end="")
    print(" " if count < 10 else "", end="")
    if assume:
        for i in range(assume):
            print("| ", end="")


def and_i(arg1, arg2, index1, index2, count, assume=None):
    """
    deal with p,q -> p&q
    """
    prop = And(arg1, arg2)
    print_prefix(count, assume)
    print(f"| {prop}--AndI {index1 + 1},{index2 + 1}")
    count += 1
    return prop, count


def and_e(arg, index, count, assume=None):
    """
    deal with p&q -> p, p&q -> q
    """
    prop = [arg.args[0], arg.args[1]]
    for ele in prop:
        print_prefix(count, assume)
        print(f"| {ele}--AndE {index + 1}")
        count += 1
    return prop, count


def or_i(arg1, arg2, index, count, assume=None):
    """
    deal with p -> p|q
    """
    prop = Or(arg1, arg2)
    print_prefix(count, assume)
    print(f"| {prop}--OrI {index + 1}")
    count += 1
    return prop, count


def if_e(arg, index1, index2, count, assume=None):
    """
    deal with a,a>b -> b
    """
    prop = arg.args[1]
    print_prefix(count, assume)
    print(f"| {prop}--IfE {index1 + 1},{index2 + 1}")
    count += 1
    return prop, count


def bottom(arg1, arg2, index1, index2, count, assume):
    """
    deal with p&~p -> F
    """
    if arg2:
        prop, count = and_i(arg1, arg2, index1, index2, count, assume=assume)

    print_prefix(count, assume)
    print(f"| F--ExFalsoQuodlibet {count - 1}")
    count += 1
    return 'bottom', count


'''Derived rules'''


def de_morgan(arg, index, count, direction=None, assume=None):
    """
    deal with ~(p|q) -> ~p&~q, ~(p&q) -> ~p|~q, ~p&~q -> ~(p|q), ~p|~q -> ~(p&q)
    """
    if direction:
        prop1 = arg.args[0].args[0] if isinstance(arg.args[0], Not) else Not(arg.args[0])
        prop2 = arg.args[1].args[0] if isinstance(arg.args[1], Not) else Not(arg.args[1])
        if isinstance(arg, Or):
            prop = Not(And(prop1, prop2))

        else:  # isinstance(arg, And)
            prop = Not(Or(prop1, prop2))

        print_prefix(count, assume)
        print(f"| {prop}--DeMorgan {index}")
        count += 1
        return prop, count

    else:
        if isinstance(arg.args[0], If):
            prop1 = arg.args[0].args[0]
        else:
            prop1 = arg.args[0].args[0].args[0] if isinstance(arg.args[0].args[0], Not) else Not(arg.args[0].args[0])

        prop2 = arg.args[0].args[1].args[0] if isinstance(arg.args[0].args[1], Not) else Not(arg.args[0].args[1])

        if isinstance(arg.args[0], Or) or isinstance(arg.args[0], If):
            prop = And(prop1, prop2)
        else:  # isinstance(arg.args[0], And)
            prop = Or(prop1, prop2)

        print_prefix(count, assume)
        print(f"| {prop}--DeMorgan {index + 1}")
        count += 1
        return prop, count


def double_negation(arg, index, count, direction=None, assume=None):
    """
    deal with p -> ~~p, ~~p -> p
    """
    if direction:
        prop = Not(Not(arg.args[0].args[0]))
    else:
        prop = arg.args[0].args[0]

    print_prefix(count, assume)
    print(f"| {prop}--DoubleNegation {index + 1}")
    count += 1
    return prop, count


def modus_tollens(arg, index1, index2, count, assume=None):
    """
    deal with ~q, p>q -> ~p
    """
    prop = arg.args[0].args[0] if isinstance(arg, Not) else Not(arg.args[0])

    print_prefix(count, assume)
    print(f"| {prop}--ModusTollens {index1 + 1},{index2 + 1}")
    count += 1
    return prop, count


def modus_tollendo_ponens(arg1, arg2, index1, index2, count, assume=None):
    """
    deal with ~p, p|q -> q, ~q, p|q -> p
    """
    prop = arg1.args[0] if isinstance(arg1, Not) else Not(arg1)
    if duplicates(prop, arg2.args[0]):
        prop = arg2.args[1]
    else:
        prop = arg2.args[0]

    print_prefix(count, assume)
    print(f"| {prop}--ModusTollendoPonens {index1 + 1},{index2 + 1}")
    count += 1
    return prop, count
