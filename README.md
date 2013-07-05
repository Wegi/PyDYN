PyDYN - Python Dependencies You Need
=====

A proof of concept for a better python dependency management

__Dependencies:__

* PBO format compatible solver 
* distribute OR setuptools installed on System
* meta.json in executing dir


__How to Use:__

1. Make sure the dir from which PyDYN is executed contains the meta.json file.
2. import pydyn.api - the other modules should no be used independently.
3. Instanciate an object from the pydyn.api.Problem class. 
    1. The only needed parameter is the package name for which you want to calculate the dependencies. 
    2. The solver argument if unchanged looks for the wbo solver (in the ./wbo/ dir). 
    3. If you change it, use the same syntax you would use in the shell to execute the solver. (without options)
    4. If you change the solver argument, don't forget to change SolverOptions as well.
    5. SolverOptions is a list of comandline options for the solver. If you don't have any use an empty list. ([])
4. The Problem object has a solve() method which returns a pydyn.api.Solution object.
5. The Solution object has several methods to output the solution to the dependencie resolution problem.


__Licence:__

The MIT License (MIT)

Copyright (c) 2013 Alexander Schneider

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
