# Benchmark

## Description

Scripts and notebooks to reproduce the experiments of our papers.

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

Use our scripts to compare the tools on a given list of instances:
- `./reduction/run_reductions.sh instances/INPUTS instances/MCC2021_list/pt_list` for the reduction analysis
- `./marking_reachability.sh instances/INPUTS instances/paper_lists/marking_reachability_list` for the marking reachability analysis
- `./concurrent_places/complete_computations.sh instances/INPUTS instances/paper_lists/concurrent_places_list` for the concurrency matrices analysis
- `./concurrent_places/partial_computations.sh instances/INPUTS instances/paper_lists/concurrent_places_list` for the partial concurrency matrices analysis

### 5) Generate summary files

Summary files can be generated using the scripts `out2csv.py` in the different subdirectories.  

Example: `./concurrent_places/out2csv.py concurrent_places/OUTPUTS`

The output `.csv` fill will be generated in the `csv/` directory.

### 6) Analyze the data

To analyze the data we provide different notebooks in the `notebooks/` directory.

To run Jupyter notebook run the command: `jupyter notebook`. After opening one of the notebooks, run all the cells by clicking on `Cell -> Run All`. The figures will be generated in the different `pics/` subdirectories.