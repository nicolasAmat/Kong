# Benchmark

## Description

Scripts and notebooks to reproduce the experiments of our papers.

## Additional requirements

+ Jupyter notebook
+ `numpy`, `matplotlib` and `pandas` Python packages
+ [pnml2nupn](https://github.com/lip6/pnml2nupn), and set the environment variable `PNML2NUPN` to the path of the `.jar` archive

## Usage

### 1) Install inputs

```$> instances/install_inputs.sh```

### 2) Generate lists of instances

To generate the list of safe nets run:  
```$> instances/get_safe_instances.py instances/INPUTS safe_list```

To generate the list of colorblind nets run:  
```$> instances/get_pt_instances.py instances/INPUTS pt_list```

Optionally you can proceed to a manual selection of instances by removing some occurrences in `safe_list` or `pt_list`.  

Our selection of instances for our papers is available in `instances/paper_lists/`. We also provide the lists corresponding to the models of the Model Checking Contest 2021 in `instances/MCC_2021_lists/`.

### 4) Run experiments

Use our scripts to run the tools on a given list of instances:
-  Reduction analysis:  
`./reduction/run_reductions.sh instances/INPUTS instances/MCC2021_list/pt_list`
- Marking reachability analysis:  
`./marking_reachability.sh instances/INPUTS instances/paper_lists/marking_reachability_list` 
- Complete concurrency matrices:  
`./concurrent_places/complete_computations.sh instances/INPUTS instances/paper_lists/concurrent_places_list`
- Partial concurrency matrices analysis:  
`./concurrent_places/partial_computations.sh instances/INPUTS instances/paper_lists/concurrent_places_list`

### 5) Generate summary files

Summary files can be generated using the `out2csv.py` scripts included in the different subdirectories (`reduction/`, `marking_reachability/` and `concurrent_places/`).  

**Example**: `./concurrent_places/out2csv.py concurrent_places/OUTPUTS/`

The summary `.csv` files will be automatically generated in the `csv/` directory.

### 6) Analyze the data

To analyze the data we provide different notebooks in the `notebooks/` subdirectory.

To run Jupyter notebook run the command: `jupyter notebook`. After opening a notebook of interest, run all the cells by clicking on `Cell -> Run All`. The figures will be generated in the `pics/` subdirectories.