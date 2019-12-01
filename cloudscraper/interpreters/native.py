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

            jsfuckChallenge = re.search(
                r"setTimeout\(function\(\){\s+var.*?f,\s*(?P<variable>\w+).*?:(?P<init>\S+)};"
                r".*?\('challenge-form'\);\s+;(?P<challenge>.*?a\.value)"
                r"(?:.*id=\"cf-dn-.*?>(?P<k>\S+)<)?",
                body,
                re.DOTALL | re.MULTILINE
            ).groupdict()

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

            if not jsfuckChallenge['k'] and '+ t.length' in body:
                jschl_answer += len(domain)

            # ------------------------------------------------------------------------------- #

            return '{0:.10f}'.format(jschl_answer)

        # ------------------------------------------------------------------------------- #

        return challengeSolve(body, domain)


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
