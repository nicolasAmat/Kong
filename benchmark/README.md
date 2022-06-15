# Benchmark

## Description

## Usage

1) Install inputs

```$> instances/install_inputs.sh```

2) Generate lists of instances

To generate the list of safe nets run:  
```$> instances/get_safe_instances.py instances/INPUTS safe_list```

To generate the list of colorblind nets run:  
```$> instances/get_pt_instances.py instances/INPUTS pt_list```

Optionally you can proceed to a manual selection of instances by removing some occurences in `safe_list` or `pt_list`. Our selection of instances for our papers is available in `instances/paper_lists/`.


