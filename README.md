# SMT-EC

This is a modern implementation of SMT-based example completion for reactive synthesis using antichain data structures.
This is based on the theory published here: To be updated.
   
# Dependencies

This program depends on:
- [Synth-Learn](https://github.com/mrudu/synth-learn): A modified version is included as a submodule in this repository.
- [Acacia-Bonsai](https://github.com/gaperez64/acacia-bonsai): A modified version is included as a submodule in this repository.
- [Pysmt](https://github.com/pysmt/pysmt): Pysmt is installed as a python package.

# Installation

To compile and run, please follow the following order to build/install the dependencies,
    1. Acacia-bonsai
    2. Synth-Learn
    3. pysmt

To build the Acacia-bonsai, first check the repository [page](https://github.com/gaperez64/acacia-bonsai) to make sure you have the dependencies, then run the following code,
```
$ cd acacia-bonsai
$ meson setup build
$ cd build
$ meson compile
```

For synth-learn, there is no need to build from the source, please again check the repository [page](https://github.com/mrudu/synth-learn) to ensure all the dependencies are installed.

# Run
The input and output are all stored under the folder examples, to switch between different input sets, modify the following line in ECtest.py
```
$ path = "..."
```

Then run the following code to call the solver
```
$ python ECtest.py
```

The synthesized machine is stored in the same file in the format of pdf.
