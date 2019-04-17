MAPPING = {
    'a': '(false+"")[1]',
    'b': '([]["entries"]()+"")[2]',
    'c': '([]["fill"]+"")[3]',
    'd': '(undefined+"")[2]',
    'e': '(true+"")[3]',
    'f': '(false+"")[0]',
    'g': '(false+[0]+String)[20]',
    'h': '(+(101))["to"+String["name"]](21)[1]',
    'i': '([false]+undefined)[10]',
    'j': '([]["entries"]()+"")[3]',
    'k': '(+(20))["to"+String["name"]](21)',
    'l': '(false+"")[2]',
    'm': '(Number+"")[11]',
    'n': '(undefined+"")[1]',
    'o': '(true+[]["fill"])[10]',
    'p': '(+(211))["to"+String["name"]](31)[1]',
    'q': '(+(212))["to"+String["name"]](31)[1]',
    'r': '(true+"")[1]',
    's': '(false+"")[3]',
    't': '(true+"")[0]',
    'u': '(undefined+"")[0]',
    'v': '(+(31))["to"+String["name"]](32)',
    'w': '(+(32))["to"+String["name"]](33)',
    'x': '(+(101))["to"+String["name"]](34)[1]',
    'y': '(NaN+[Infinity])[10]',
    'z': '(+(35))["to"+String["name"]](36)',
    'A': '(+[]+Array)[10]',
    'B': '(+[]+Boolean)[10]',
    'C': 'Function("return escape")()(("")["italics"]())[2]',
    'D': 'Function("return escape")()([]["fill"])["slice"]("-1")',
    'E': '(RegExp+"")[12]',
    'F': '(+[]+Function)[10]',
    'G': '(false+Function("return Date")()())[30]',
    'I': '(Infinity+"")[0]',
    'M': '(true+Function("return Date")()())[30]',
    'N': '(NaN+"")[0]',
    'O': '(NaN+Function("return{}")())[11]',
    'R': '(+[]+RegExp)[10]',
    'S': '(+[]+String)[10]',
    'T': '(NaN+Function("return Date")()())[30]',
    'U': '(NaN+Function("return{}")()["to"+String["name"]]["call"]())[11]',
    ' ': '(NaN+[]["fill"])[11]',
    '"': '("")["fontcolor"]()[12]',
    '%': 'Function("return escape")()([]["fill"])[21]',
    '&': '("")["link"](0+")[10]',
    '(': '(undefined+[]["fill"])[22]',
    ')': '([0]+false+[]["fill"])[20]',
    '+': '(+(+!+[]+(!+[]+[])[!+[]+!+[]+!+[]]+[+!+[]]+[+[]]+[+[]])+[])[2]',
    ',': '([]["slice"]["call"](false+"")+"")[1]',
    '-': '(+(.+[0000000001])+"")[2]',
    '.': '(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]',
    '/': '(false+[0])["italics"]()[10]',
    ':': '(RegExp()+"")[3]',
    ';': '("")["link"](")[14]',
    '<': '("")["italics"]()[0]',
    '=': '("")["fontcolor"]()[11]',
    '>': '("")["italics"]()[2]',
    '?': '(RegExp()+"")[2]',
    '[': '([]["entries"]()+"")[0]',
    ']': '([]["entries"]()+"")[22]',
    '{': '(true+[]["fill"])[20]',
    '}': '([]["fill"]+"")["slice"]("-1")'
}

SIMPLE = {
    'false': '![]',
    'true': '!![]',
    'undefined': '[][[]]',
    'NaN': '+[![]]',
    'Infinity': '+(+!+[]+(!+[]+[])[!+[]+!+[]+!+[]]+[+!+[]]+[+[]]+[+[]]+[+[]])'  # +"1e1000"
}

CONSTRUCTORS = {
    'Array': '[]',
    'Number': '(+[])',
    'String': '([]+[])',
    'Boolean': '(![])',
    'Function': '[]["fill"]',
    'RegExp': 'Function("return/"+false+"/")()'
}


def jsunfuck(jsfuckString):
    for key in sorted(MAPPING, key=lambda k: len(MAPPING[k]), reverse=True):
        if MAPPING.get(key) in jsfuckString:
            jsfuckString = jsfuckString.replace(MAPPING.get(key), '"{}"'.format(key))

    for key in sorted(SIMPLE, key=lambda k: len(SIMPLE[k]), reverse=True):
        if SIMPLE.get(key) in jsfuckString:
            jsfuckString = jsfuckString.replace(SIMPLE.get(key), '{}'.format(key))

    # for key in sorted(CONSTRUCTORS, key=lambda k: len(CONSTRUCTORS[k]), reverse=True):
    #    if CONSTRUCTORS.get(key) in jsfuckString:
    #        jsfuckString = jsfuckString.replace(CONSTRUCTORS.get(key), '{}'.format(key))

    return jsfuckString
