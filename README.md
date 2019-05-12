ChakraCore
=================
ChakraCore is the core part of Chakra, the high-performance JavaScript engine that powers Microsoft Edge and Windows applications written in HTML/CSS/JS.  ChakraCore supports Just-in-time (JIT) compilation of JavaScript for x86/x64/ARM, garbage collection, and a wide range of the latest JavaScript features.  ChakraCore also supports the [JavaScript Runtime (JSRT) APIs](https://github.com/Microsoft/ChakraCore/wiki/JavaScript-Runtime-%28JSRT%29-Overview), which allows you to easily embed ChakraCore in your applications.

You can stay up-to-date on progress by following the [MSEdge developer blog](https://blogs.windows.com/msedgedev/).

Offical microsoft releases can be found [here](https://github.com/microsoft/ChakraCore).

Installation
============

Simply copy the library for your OS into your project working directory or into one of your system library directories.

An example for linux would be.

```
cp Linux-x86_64/libChakraCore.so /usr/local/lib/
ldconfig
```
