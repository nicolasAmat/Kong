# Kong: Koncurrent Place Squasher

## About

Kong is a tool to compute the concurrency relation of a Petri using net reduction.

## Requirements

+ Python >+ 3.5
+ caesar.bdd from the [CADP Toolbox](https://cadp.inria.fr/)
+ reduce tool from the [TINA Toolbox](http://projects.laas.fr/tina/)
+ [PNML2NUPN](https://github.com/lip6/pnml2nupn) tool

## Running the Tool

Before running the tool you need to export the `PNML2NUPN` environment variable to indicate the path to the PNML2NUPN Java Archive:
```
$> export PNML2NUPN=<path_to_.jar>
```

Run **Kong** by indicating the path to the input Petri net (`.pnml` format):
```
$> ./kong.py <path_to_.pnml>
```

You can list all the options by using the *help* option:
```
$> ./kong.py --help
usage: kong.py [-h] [--version] [-v] [-pl] filename

Koncurrent Places Squasher

positional arguments:
  filename            input Petri net (.pnml format)

optional arguments:
  -h, --help          show this help message and exit
  --version           show the version number and exit
  -v, --verbose       increase output verbosity
  -pl, --place_names  display place names
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