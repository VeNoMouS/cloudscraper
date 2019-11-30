from __future__ import absolute_import

import os
import sys
import ctypes.util

from ctypes import c_void_p, c_size_t, byref, create_string_buffer, CDLL

from . import JavaScriptInterpreter
from .encapsulated import template

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    # ------------------------------------------------------------------------------- #

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('chakracore')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):
        chakraCoreLibrary = None

        # check current working directory.
        for _libraryFile in ['libChakraCore.so', 'libChakraCore.dylib', 'ChakraCore.dll']:
            if os.path.isfile(os.path.join(os.getcwd(), _libraryFile)):
                chakraCoreLibrary = os.path.join(os.getcwd(), _libraryFile)
                continue

        if not chakraCoreLibrary:
            chakraCoreLibrary = ctypes.util.find_library('ChakraCore')

        if not chakraCoreLibrary:
            sys.tracebacklimit = 0
            raise RuntimeError(
                'ChakraCore library not found in current path or any of your system library paths, '
                'please download from https://www.github.com/VeNoMouS/cloudscraper/tree/ChakraCore/, '
                'or https://github.com/Microsoft/ChakraCore/'
            )

        try:
            chakraCore = CDLL(chakraCoreLibrary)
        except OSError:
            sys.tracebacklimit = 0
            raise RuntimeError('There was an error loading the ChakraCore library {}'.format(chakraCoreLibrary))

        if sys.platform != 'win32':
            chakraCore.DllMain(0, 1, 0)
            chakraCore.DllMain(0, 2, 0)

        script = create_string_buffer(template(body, domain).encode('utf-16'))

        runtime = c_void_p()
        chakraCore.JsCreateRuntime(0, 0, byref(runtime))

        context = c_void_p()
        chakraCore.JsCreateContext(runtime, byref(context))
        chakraCore.JsSetCurrentContext(context)

        fname = c_void_p()
        chakraCore.JsCreateString(
            'iuam-challenge.js',
            len('iuam-challenge.js'),
            byref(fname)
        )

        scriptSource = c_void_p()
        chakraCore.JsCreateExternalArrayBuffer(
            script,
            len(script),
            0,
            0,
            byref(scriptSource)
        )

        jsResult = c_void_p()
        chakraCore.JsRun(scriptSource, 0, fname, 0x02, byref(jsResult))

        resultJSString = c_void_p()
        chakraCore.JsConvertValueToString(jsResult, byref(resultJSString))

        stringLength = c_size_t()
        chakraCore.JsCopyString(resultJSString, 0, 0, byref(stringLength))

        resultSTR = create_string_buffer(stringLength.value + 1)
        chakraCore.JsCopyString(
            resultJSString,
            byref(resultSTR),
            stringLength.value + 1,
            0
        )

        chakraCore.JsDisposeRuntime(runtime)

        return resultSTR.value


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
