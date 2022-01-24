# Kong: Koncurrent places Grinder

<br />
<p align="center">
  <a href="https://github.com/nicolasAmat/Kong">
    <img src="logo.png" alt="Logo" width="256" height="258">
  </a>
</p>

## About

Kong is a tool to compute the concurrency relation of a Petri using net reduction.

## Requirements

+ Python >+ 3.5
+ caesar.bdd from the [CADP Toolbox](https://cadp.inria.fr/)
+ reduce and ndrio tools from the [TINA Toolbox](http://projects.laas.fr/tina/)
+ (optional) [graphviz](https://pypi.org/project/graphviz/)

## Running the Tool

Run **Kong** by indicating the path to the input Petri net (`.pnml` or `.nupn` format):
```
$> ./kong.py <path_to_.pnml>
```

You can list all the options by using the *help* option:
```
$> ./kong.py --help
usage: kong.py [-h] [--version] [-v] [-sr | -r REDUCED_NET] [-pl] [-t] [-sn] [-srr] [-se] [-srm] [-dg]
               [--bdd-timeout BDD_TIMEOUT] [--bdd-iterations BDD_ITERATIONS]
               filename

Koncurrent places Grinder

positional arguments:
  filename              input Petri net (.pnml or .nupn format)

optional arguments:
  -h, --help            show this help message and exit
  --version             show the version number and exit
  -v, --verbose         increase output verbosity
  -sr, --save-reduced   save the reduced net
  -r REDUCED_NET, --reduced REDUCED_NET
                        reduced Petri Net (.net format)
  -pl, --place-names    show place names
  -t, --time            show the computation time
  -sn, --show-nupns     show the NUPNs
  -srr, --show-reduction-ratio
                        show the reduction ratio
  -se, --show-equations
                        show the reduction equations
  -srm, --show-reduced-matrix
                        show the reduced matrix
  -dg, --draw-graph     draw the Token Flow Graph
  --bdd-timeout BDD_TIMEOUT
                        set the time limit for marking graph exploration (caesar.bdd)
  --bdd-iterations BDD_ITERATIONS
                        set the limit for number of iterations for marking graph exploration (caesar.bdd)
```

## Performance Evaluation

The code repository includes a reproducible performance evaluation in the `benchmark/` directory.  
Jupyter is needed to run the code.

## Dependencies

The code repository includes a link to models from the [MCC Petri Nets
Repository](https://pnrepository.lip6.fr/) used for benchmarking and
continuous testing.

## License

This software is distributed under the
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.
A copy of the license agreement is found in the [LICENSE](./LICENSE) file.

## Authors

+ **Nicolas AMAT** -  [LAAS/CNRS](https://www.laas.fr/)