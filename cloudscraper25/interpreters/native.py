from __future__ import absolute_import

import ast
import re
import operator as op
import pyparsing

from ..exceptions import CloudflareSolveError
from . import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #

_OP_MAP = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Invert: op.neg,
}

# ------------------------------------------------------------------------------- #


class Calc(ast.NodeVisitor):

    def visit_BinOp(self, node):
        return _OP_MAP[type(node.op)](self.visit(node.left), self.visit(node.right))

    # ------------------------------------------------------------------------------- #

    def visit_Num(self, node):
        return node.n

    # ------------------------------------------------------------------------------- #

    def visit_Expr(self, node):
        return self.visit(node.value)

    # ------------------------------------------------------------------------------- #

    @classmethod
    def doMath(cls, expression):
        tree = ast.parse(expression)
        calc = cls()
        return calc.visit(tree.body[0])

# ------------------------------------------------------------------------------- #


class Parentheses(object):

    def fix(self, s):
        res = []
        self.visited = set([s])
        self.dfs(s, self.invalid(s), res)
        return res

    # ------------------------------------------------------------------------------- #

    def dfs(self, s, n, res):
        if n == 0:
            res.append(s)
            return
        for i in range(len(s)):
            if s[i] in ['(', ')']:
                s_new = s[:i] + s[i + 1:]
                if s_new not in self.visited and self.invalid(s_new) < n:
                    self.visited.add(s_new)
                    self.dfs(s_new, self.invalid(s_new), res)

    # ------------------------------------------------------------------------------- #

    def invalid(self, s):
        plus = minus = 0
        memo = {"(": 1, ")": -1}
        for c in s:
            plus += memo.get(c, 0)
            minus += 1 if plus < 0 else 0
            plus = max(0, plus)
        return plus + minus

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('native')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):

        operators = {
            '+': op.add,
            '-': op.sub,
            '*': op.mul,
            '/': op.truediv
        }

        # ------------------------------------------------------------------------------- #

        def flatten(lists):
            return sum(map(flatten, lists), []) if isinstance(lists, list) else [lists]

        # ------------------------------------------------------------------------------- #

        def jsfuckToNumber(jsFuck):
            # "Clean Up" JSFuck
            jsFuck = jsFuck.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0')
            jsFuck = jsFuck.lstrip('+').replace('(+', '(').replace(' ', '')
            jsFuck = Parentheses().fix(jsFuck)[0]

            # Hackery Parser for Math
            stack = []
            bstack = []

            for i in flatten(pyparsing.nestedExpr().parseString(jsFuck).asList()):
                if i == '+':
                    stack.append(bstack)
                    bstack = []
                    continue
                bstack.append(i)
            stack.append(bstack)

            return int(''.join([str(Calc.doMath(''.join(i))) for i in stack]))

        # ------------------------------------------------------------------------------- #

        def divisorMath(payload, needle, domain):
            jsfuckMath = payload.split('/')
            if needle in jsfuckMath[1]:
                expression = re.findall(r"^(.*?)(.)\(function", jsfuckMath[1])[0]

                expression_value = operators[expression[1]](
                    float(jsfuckToNumber(expression[0])),
                    float(ord(domain[jsfuckToNumber(jsfuckMath[1][
                        jsfuckMath[1].find('"("+p+")")}') + len('"("+p+")")}'):-2
                    ])]))
                )
            else:
                expression_value = jsfuckToNumber(jsfuckMath[1])

            expression_value = jsfuckToNumber(jsfuckMath[0]) / float(expression_value)

            return expression_value

        # ------------------------------------------------------------------------------- #

        def challengeSolve(body, domain):
            jschl_answer = 0

            try:
                jsfuckChallenge = re.search(
                    r"setTimeout\(function\(\){\s+var.*?f,\s*(?P<variable>\w+).*?:(?P<init>\S+)};"
                    r".*?\('challenge-form'\);.*?;(?P<challenge>.*?a\.value)\s*=\s*\S+\.toFixed\(10\);",
                    body,
                    re.DOTALL | re.MULTILINE
                ).groupdict()
            except AttributeError:
                raise CloudflareSolveError('There was an issue extracting "jsfuckChallenge" from the Cloudflare challenge.')

            kJSFUCK = re.search(r'(;|)\s*k.=(?P<kJSFUCK>\S+);', jsfuckChallenge['challenge'], re.S | re.M)
            if kJSFUCK:
                try:
                    kJSFUCK = jsfuckToNumber(kJSFUCK.group('kJSFUCK'))
                except IndexError:
                    raise CloudflareSolveError('There was an issue extracting "kJSFUCK" from the Cloudflare challenge.')

                try:
                    kID = re.search(r"\s*k\s*=\s*'(?P<kID>\S+)';", body).group('kID')
                except IndexError:
                    raise CloudflareSolveError('There was an issue extracting "kID" from the Cloudflare challenge.')

                try:
                    r = re.compile(r'<div id="{}(?P<id>\d+)">\s*(?P<jsfuck>[^<>]*)</div>'.format(kID))

                    kValues = {}
                    for m in r.finditer(body):
                        kValues[int(m.group('id'))] = m.group('jsfuck')

                    jsfuckChallenge['k'] = kValues[kJSFUCK]
                except (AttributeError, IndexError):
                    raise CloudflareSolveError('There was an issue extracting "kValues" from the Cloudflare challenge.')

            jsfuckChallenge['challenge'] = re.finditer(
                r'{}.*?([+\-*/])=(.*?);(?=a\.value|{})'.format(
                    jsfuckChallenge['variable'],
                    jsfuckChallenge['variable']
                ),
                jsfuckChallenge['challenge']
            )

            # ------------------------------------------------------------------------------- #

            if '/' in jsfuckChallenge['init']:
                val = jsfuckChallenge['init'].split('/')
                jschl_answer = jsfuckToNumber(val[0]) / float(jsfuckToNumber(val[1]))
            else:
                jschl_answer = jsfuckToNumber(jsfuckChallenge['init'])

            # ------------------------------------------------------------------------------- #

            for expressionMatch in jsfuckChallenge['challenge']:
                oper, expression = expressionMatch.groups()

                if '/' in expression:
                    expression_value = divisorMath(expression, 'function(p)', domain)
                else:
                    if 'Element' in expression:
                        expression_value = divisorMath(jsfuckChallenge['k'], '"("+p+")")}', domain)
                    else:
                        expression_value = jsfuckToNumber(expression)

                jschl_answer = operators[oper](jschl_answer, expression_value)

            # ------------------------------------------------------------------------------- #

            # if not jsfuckChallenge['k'] and '+ t.length' in body:
            #    jschl_answer += len(domain)

            # ------------------------------------------------------------------------------- #

            return '{0:.10f}'.format(jschl_answer)

        # ------------------------------------------------------------------------------- #

        return challengeSolve(body, domain)

# ------------------------------------------------------------------------------- #


ChallengeInterpreter()
