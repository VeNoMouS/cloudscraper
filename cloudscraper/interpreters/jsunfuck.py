#!/bin/env python
# -*- coding:utf-8 -*-

MAPPING = {
    "a": '(false+"")[1]',
    "b": '([]["entries"]()+"")[2]',
    "c": '([]["fill"]+"")[3]',
    "d": '(undefined+"")[2]',
    "e": '(true+"")[3]',
    "f": '(false+"")[0]',
    "g": "(false+[0]+String)[20]",
    "h": '(+(101))["to"+String["name"]](21)[1]',
    "i": "([false]+undefined)[10]",
    "j": '([]["entries"]()+"")[3]',
    "k": '(+(20))["to"+String["name"]](21)',
    "l": '(false+"")[2]',
    "m": '(Number+"")[11]',
    "n": '(undefined+"")[1]',
    "o": '(true+[]["fill"])[10]',
    "p": '(+(211))["to"+String["name"]](31)[1]',
    "q": '(+(212))["to"+String["name"]](31)[1]',
    "r": '(true+"")[1]',
    "s": '(false+"")[3]',
    "t": '(true+"")[0]',
    "u": '(undefined+"")[0]',
    "v": '(+(31))["to"+String["name"]](32)',
    "w": '(+(32))["to"+String["name"]](33)',
    "x": '(+(101))["to"+String["name"]](34)[1]',
    "y": "(NaN+[Infinity])[10]",
    "z": '(+(35))["to"+String["name"]](36)',
    "A": '(NaN+[]["entries"]())[11]',
    "B": "(+[]+Boolean)[10]",
    "C": 'Function("return escape")()(("")["italics"]())[2]',
    "D": 'Function("return escape")()([]["fill"])["slice"]("-1")',
    "E": '(RegExp+"")[12]',
    "F": "(+[]+Function)[10]",
    "G": '(false+Function("return Date")()())[30]',
    "H": None,
    "I": '(Infinity+"")[0]',
    "J": None,
    "K": None,
    "L": None,
    "M": '(true+Function("return Date")()())[30]',
    "N": '(NaN+"")[0]',
    "O": "(+[]+Object)[10]",
    "P": None,
    "Q": None,
    "R": "(+[]+RegExp)[10]",
    "S": "(+[]+String)[10]",
    "T": '(NaN+Function("return Date")()())[30]',
    "U": '(NaN+Object()["to"+String["name"]]["call"]())[11]',
    "V": None,
    "W": None,
    "X": None,
    "Y": None,
    "Z": None,
    " ": '(NaN+[]["fill"])[11]',
    "!": None,
    '"': '("")["fontcolor"]()[12]',
    "#": None,
    "$": None,
    "%": 'Function("return escape")()([]["fill"])[21]',
    "&": '("")["link"](0+")[10]',
    "'": None,
    "(": '([]["fill"]+"")[13]',
    ")": '([0]+false+[]["fill"])[20]',
    "*": None,
    "+": "(+(+!+[]+(!+[]+[])[!+[]+!+[]+!+[]]+[+!+[]]+[+[]]+[+[]])+[])[2]",
    ",": '[[]]["concat"]([[]])+""',
    "-": '(+(.+[0000001])+"")[2]',
    ".": "(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]",
    "/": '(false+[0])["italics"]()[10]',
    ":": '(RegExp()+"")[3]',
    ";": '("")["link"](")[14]',
    "<": '("")["italics"]()[0]',
    "=": '("")["fontcolor"]()[11]',
    ">": '("")["italics"]()[2]',
    "?": '(RegExp()+"")[2]',
    "@": None,
    "[": '([]["entries"]()+"")[0]',
    "\\": '(RegExp("/")+"")[1]',
    "]": '([]["entries"]()+"")[22]',
    "^": None,
    "_": None,
    "`": None,
    "{": '(true+[]["fill"])[20]',
    "|": None,
    "}": '([]["fill"]+"")["slice"]("-1")',
    "~": None,
}

SIMPLE = {
    "false": "![]",
    "true": "!![]",
    "undefined": "[][[]]",
    "NaN": "+[![]]",
    "Infinity": "+(+!+[]+(!+[]+[])[!+[]+!+[]+!+[]]+[+!+[]]+[+[]]+[+[]]+[+[]])",  # +"1e1000"
}

CONSTRUCTORS = {
    "Array": "[]",
    "Number": "(+[])",
    "String": "([]+[])",
    "Boolean": "(![])",
    "Function": '[]["fill"]',
    "RegExp": 'Function("return/"+false+"/")()',
    "Object": '[]["entries"]()',
}

GLOBAL = 'Function("return this")()'


def jsunfuck(jsfuckString):
    for key in sorted(MAPPING, key=lambda k: len(MAPPING[k]), reverse=True):
        if MAPPING.get(key) in jsfuckString:
            jsfuckString = jsfuckString.replace(MAPPING.get(key), '"{}"'.format(key))

    for key in sorted(SIMPLE, key=lambda k: len(SIMPLE[k]), reverse=True):
        if SIMPLE.get(key) in jsfuckString:
            jsfuckString = jsfuckString.replace(SIMPLE.get(key), "{}".format(key))

    # for key in sorted(CONSTRUCTORS, key=lambda k: len(CONSTRUCTORS[k]), reverse=True):
    #    if CONSTRUCTORS.get(key) in jsfuckString:
    #        jsfuckString = jsfuckString.replace(CONSTRUCTORS.get(key), '{}'.format(key))

    return jsfuckString
