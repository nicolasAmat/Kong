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
+ `caesar.bdd` from the [CADP Toolbox](https://cadp.inria.fr/) (only for the `conc` and `dead` subcommands)
+ `sift` from the [TINA Toolbox](http://projects.laas.fr/tina/) (only for the `reach` subcommand)
+ `reduce` and ndrio tools from the [TINA Toolbox](http://projects.laas.fr/tina/)
+ (optional) [graphviz](https://pypi.org/project/graphviz/) python package

## Running the Tool

Run **Kong** by selecting a subcommand (`conc` `dead`, or `reach`) and indicating the path to the input Petri net (`.pnml` or `.nupn` format):
```
$> ./kong.py {conc, dead, reach} {<path_to_.pnml>, <path_to_.nupn>}
```

You can list all the subcommands and options by using the *help* option:
```
$> ./kong.py --help
usage: kong.py [-h] [--version] {conc,dead,reach} ...

Koncurrent places Grinder

positional arguments:
  {conc,dead,reach}  Mode
    conc             Concurrent places computation
    dead             Dead places computation
    reach            Marking reachability decision

options:
  -h, --help         show this help message and exit
  --version          show the version number and exit
```

Similarly, you can list the options of each subcommand:

`conc`:
```
$> ./kong.py conc --help
usage: kong.py conc [-h] [-v] [-sk] [-sr | -rn REDUCED_NET] [-t] [-srr] [-se] [-dg] [-nu] [-nr] [-pl] [-sn] [--bdd-timeout BDD_TIMEOUT] [--bdd-iterations BDD_ITERATIONS]
                    [-rm REDUCED_RESULT] [-srm]
                    filename

positional arguments:
  filename              input Petri net (.pnml or .nupn format)

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -sk, --shrink         use the Shrink reduction tool
  -sr, --save-reduced-net
                        save the reduced net
  -rn REDUCED_NET, --reduced-net REDUCED_NET
                        specify reduced Petri net (.net format)
  -t, --time            show the computation time
  -srr, --show-reduction-ratio
                        show the reduction ratio
  -se, --show-equations
                        show the reduction equations
  -dg, --draw-graph     draw the Token Flow Graph
  -nu, --no-units       disable units propagation
  -nr, --no-rle         disable run-length encoding (RLE)
  -pl, --place-names    show place names
  -sn, --show-nupns     show the NUPNs
  --bdd-timeout BDD_TIMEOUT
                        set the time limit for marking graph exploration (caesar.bdd)
  --bdd-iterations BDD_ITERATIONS
                        set the limit for number of iterations for marking graph exploration (caesar.bdd)
  -rm REDUCED_RESULT, --reduced-matrix REDUCED_RESULT
                        specify reduced concurrency matrix (or dead places vector) file
  -srm, --show-reduced-matrix
                        show the reduced matrix
```

`dead`
```
$> ./kong.py dead --help
usage: kong.py dead [-h] [-v] [-sk] [-sr | -rn REDUCED_NET] [-t] [-srr] [-se] [-dg] [-nu] [-nr] [-pl] [-sn] [--bdd-timeout BDD_TIMEOUT] [--bdd-iterations BDD_ITERATIONS]
                    [-rm REDUCED_RESULT] [-srv]
                    filename

positional arguments:
  filename              input Petri net (.pnml or .nupn format)

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -sk, --shrink         use the Shrink reduction tool
  -sr, --save-reduced-net
                        save the reduced net
  -rn REDUCED_NET, --reduced-net REDUCED_NET
                        specify reduced Petri net (.net format)
  -t, --time            show the computation time
  -srr, --show-reduction-ratio
                        show the reduction ratio
  -se, --show-equations
                        show the reduction equations
  -dg, --draw-graph     draw the Token Flow Graph
  -nu, --no-units       disable units propagation
  -nr, --no-rle         disable run-length encoding (RLE)
  -pl, --place-names    show place names
  -sn, --show-nupns     show the NUPNs
  --bdd-timeout BDD_TIMEOUT
                        set the time limit for marking graph exploration (caesar.bdd)
  --bdd-iterations BDD_ITERATIONS
                        set the limit for number of iterations for marking graph exploration (caesar.bdd)
  -rm REDUCED_RESULT, --reduced-vector REDUCED_RESULT
                        specify reduced dead places vector file
  -srv, --show-reduced-vector
                        show the reduced vector
```

`reach`
```
$> ./kong.py reach --help
usage: kong.py reach [-h] [-v] [-sk] [-sr | -rn REDUCED_NET] [-t] [-srr] [-se] [-dg] [-m MARKING] [-sf] filename

positional arguments:
  filename              input Petri net (.pnml or .net format)

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -sk, --shrink         use the Shrink reduction tool
  -sr, --save-reduced-net
                        save the reduced net
  -rn REDUCED_NET, --reduced-net REDUCED_NET
                        specify reduced Petri net (.net format)
  -t, --time            show the computation time
  -srr, --show-reduction-ratio
                        show the reduction ratio
  -se, --show-equations
                        show the reduction equations
  -dg, --draw-graph     draw the Token Flow Graph
  -m MARKING, --marking MARKING
                        marking
  -sf, --show-projected-marking
                        show the projected marking
```
 
For more information, and concrete examples refer to our tool paper (see References).

## Performance Evaluation

The code repository includes a reproducible performance evaluation in the `benchmark/` directory.   (Jupyter notebook is required.)

## References

+ Amat, N., Chauvet, L. (2022). Kong: A Tool to Squash Concurrent Places. In: Bernardinello, L., Petrucci, L. (eds) Application and Theory of Petri Nets and Concurrency. PETRI NETS 2022. Lecture Notes in Computer Science, vol 13288. Springer, Cham. https://doi.org/10.1007/978-3-031-06653-5_6

+ Amat, N., Dal Zilio, S., Le Botlan, D. (2021). Accelerating the Computation of Dead and Concurrent Places Using Reductions. In: Laarman, A., Sokolova, A. (eds) Model Checking Software. SPIN 2021. Lecture Notes in Computer Science(), vol 12864. Springer, Cham. https://doi.org/10.1007/978-3-030-84629-9_3

## Dependencies

The code repository includes a link to models from the [Model Checking Contest (MCC)](https://mcc.lip6.fr/index.php) used for benchmarking and
continuous testing.

## License

This software is distributed under the
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.
A copy of the license agreement is found in the [LICENSE](./LICENSE) file.

## Authors

+ **Nicolas AMAT** -  [LAAS/CNRS](https://www.laas.fr/)