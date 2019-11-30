from __future__ import absolute_import

import re
import operator as op

from . import JavaScriptInterpreter

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('native')

    def eval(self, body, domain):
        # ------------------------------------------------------------------------------- #

        operators = {
            '+': op.add,
            '-': op.sub,
            '*': op.mul,
            '/': op.truediv
        }

        # ------------------------------------------------------------------------------- #

        def jsfuckToNumber(jsFuck):
            t = ''

            split_numbers = re.compile(r'-?\d+').findall

            for i in re.findall(
                r'\((?:\d|\+|\-)*\)',
                jsFuck.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').lstrip('+').replace('(+', '(')
            ):
                t = '{}{}'.format(t, sum(int(x) for x in split_numbers(i)))

            return int(t)

        # ------------------------------------------------------------------------------- #

        def divisorMath(payload, needle, domain):
            jsfuckMath = payload.split('/')
            if needle in jsfuckMath[1]:
                expression = re.findall(r"^(.*?)(.)\(function", jsfuckMath[1])[0]
                expression_value = operators[expression[1]](
                    float(jsfuckToNumber(expression[0])),
                    float(ord(domain[jsfuckToNumber(jsfuckMath[1][jsfuckMath[1].find('"("+p+")")}') + len('"("+p+")")}'):-2])]))
                )
            else:
                expression_value = jsfuckToNumber(jsfuckMath[1])

            expression_value = jsfuckToNumber(jsfuckMath[0]) / float(expression_value)

            return expression_value

        # ------------------------------------------------------------------------------- #

        def challengeSolve(body, domain):
            jschl_answer = 0
            jsfuckChallenge = re.search(
                r"setTimeout\(function\(\){\s+var.*?.*:(?P<init>\S+)};.*"
                r"?document\.getElementById\(\'challenge-form\'\);\s*;(?P<challenge>.*?)a\.value"
                r".*?\"\s+id=\"cf\-.*?\">(?P<k>\S+)</",
                body,
                re.DOTALL | re.MULTILINE
            ).groupdict()

            jsfuckChallenge['challenge'] = jsfuckChallenge['challenge'].replace(' return +(p)}();', '', 1).split(';')

            # ------------------------------------------------------------------------------- #

            if '/' in jsfuckChallenge['init']:
                val = jsfuckChallenge['init'].split('/')
                jschl_answer = jsfuckToNumber(val[0]) / float(jsfuckToNumber(val[1]))
            else:
                jschl_answer = jsfuckToNumber(jsfuckChallenge['init'])

            # ------------------------------------------------------------------------------- #

            for jsfuckExpression in jsfuckChallenge['challenge']:
                if not jsfuckExpression.strip():
                    continue

                oper, expression = jsfuckExpression.split('=', 1)

                if '/' in expression:
                    expression_value = divisorMath(expression, 'function(p)', domain)
                else:
                    if 'Element' in expression:
                        expression_value = divisorMath(jsfuckChallenge['k'], '"("+p+")")}', domain)
                    else:
                        expression_value = jsfuckToNumber(expression)

                jschl_answer = operators[oper[-1]](jschl_answer, expression_value)

            # ------------------------------------------------------------------------------- #

            return '{0:.10f}'.format(jschl_answer)

        # ------------------------------------------------------------------------------- #

        return challengeSolve(body, domain)


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
