#!/usr/bin/env python

import ast
import operator as op
from utilities import ini_info

# Setup logging
from utilities import logger
log = logger.get(__name__)

# Supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

is_metric = ini_info.get_is_metric()

def eval(expr):
    if expr is None or expr == '':
        return
    factor = 1
    expr = expr.lower()
    if "in" in expr or '"' in expr:
        expr = expr.replace("in", "").replace('"', "")
        if is_metric:
            factor = 25.4
    elif "mm" in expr:
        expr = expr.replace("mm", "")
        if not is_metric:
            factor = 1/25.4
    try:
        return _eval(ast.parse(expr, mode='eval').body) * factor
    except (ValueError, TypeError) as e:
        log.exception(e)

def _eval(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))
    else:
        raise TypeError(node)
