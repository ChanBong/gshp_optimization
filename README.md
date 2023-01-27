# GS_HP Optimisation 
## File Structure

### Folders
- `data`: Contains data for competetion and some other data from OML
- `hgs_vrptw`: base C++ code for HGS
- `instances`: VRPTW instances provided by ORTEC
- `notebooks`: Experiments mainly 
- `release`: compiled C++ code with python bindings
- `strategies`: dynamic and static strategies by OML

### Files

- `app.py` : Runs the flask server
- `controller.py` : Controller for static and dynamic varients. NOT WORKING 
- `enviournemnt.py`: Env for solving dynamic problems. Also used in static varient in limited capacity
- `hgspy.py`: python binding for HGS C++ release
- `main.py` : Test solutions
- `maps.py`: Everything related to mapping adrresses and all
- `models.py` : File containing all the classes of solvers used
- `solver.py`: Main solver
- `tools.py`: Various utils 

## Flask API
There is an endpoint for each model that we are using.
- `oml`: For OML solution
- `hgs`: For vanilla HGS solution
### Input

Input to any endpoint is a json file with following fields
```json
{
    instance_name: "name_of_the_instance",
    instance_seed: "seed_for_the_instance",
    solver_seed: "seed_for_the_solver",
    epoch_tlim: "time_limit_for_each_epoch",
    config_loc: "configs/solver.toml",
    profile: True,
    static: "boolean_value_wheater_we_want_to_solve_static_or_dynamic",
    hindsight: False
}
```

### Output
```json
routes:[
    {
        locationID1: 1
        locationID2: 2
        distance: "distance_travelled_by_the_rider"
    }
]
```

## Solver

Our static solver is based on the hybrid genetic search baseline we received as part of the quickstart code [here](https://github.com/ortec/euro-neurips-vrp-2022-quickstart).
We have refactored this solver significantly, making it much more modular and more performant.
We also:
- Introduced a generalised $(N, M)$-Exchange operator
- Added statistics collection
- Separated local search and intensification
- Improved parent selection for crossover by focussing on the diversity of both parents
- Simplified solution state
- Removed many ineffective parameters and constructive heuristics
- And more!

Our dynamic strategy (`simulate`) simulates requests from future epochs.
In each epoch, we simulate multiple scenarios and quickly solve the resulting simulation instances using the static solver (in a few hundred milliseconds).
We use the simulation solutions to determine which requests to postpone, and which to dispatch. 
In particular, we postpone a request if it was infrequently paired with must-dispatch requests, otherwise we dispatch it.
We then solve the resulting dispatch instance, again using the static solver. 
We also:
- Apply the simulation strategy in a recursive fashion
- Use epoch-specific thresholds to determine which requests to postpone
- Postpone routes from dispatch solutions if they do not contain any must-dispatch requests
- And more!

Finally, we tuned the static and dynamic parameters in several large-scale numerical experiments.

## How to use

First, one needs to install the required poetry dependencies:
```bash
poetry install
```
Make local folders for `solutions` and `logs`
```bash
mkdir solutions logs
```
I have already compliled the static and dynamic solver. 
**If we make some changes in C++**, then one needs to compile the static solver.
Assuming the pybind submodule has been initialised, and `cmake` is available, the following should work:
```bash
cmake -Brelease -Shgs_vrptw -DCMAKE_BUILD_TYPE=Release
make --directory=release
```
Then, the solver (both static and dynamic) can be called using the `solver.py` script.
```bash
python3 solver.py --epoch_tlim 5 --static --instance instances/toy_vrp.txt --profile
```
This doesn't work currently. It is easiest to run this via the `controller.py` script, as (e.g.):
```bash
python controller.py --instance instances/ORTEC-VRPTW-ASYM-0bdff870-d1-n458-k35.txt --epoch_tlim 5 -- python solver.py
```
This runs the solver on the given dynamic instance, with a 5s time limit per epoch.
Solving the static instance is achieved by also passing in the `--static` flag.
Additional command line options are available, and can be found in the respective scripts.

We also offer several standalone scripts running multiple instances in parallel, which is useful for benchmarking.
These scripts are:
- `analysis.py`, which runs the static solver on all instances, collects statistics, and outputs lots of useful data to a given folder.
- `benchmark.py`, which benchmarks the static solver over all instances.
- `benchmark_dynamic.py`, which benchmarks the dynamic solver over all instances.

Finally, for tuning, we used the `make_dynamic_parameters.py` and `make_static_parameters.py` scripts.
These produce configuration files that can be passed into any of the other scripts mentioned above.
To run the tuning scripts, the optional `tune` dependency group should be installed, using:
```bash
poetry install --only tune
```

## TODO

### App interaction
- [x] Run a flask app
- [ ] Feed parsed data from csv to DB
- [ ] Return the jsonified results

### OR Optimisation 

- [x] HGS-Swap*
- [x] OptiML Solution
- [ ] VNS
- [ ] OptiML pipeline

### ML Optimisation

- [ ] Kleopetra
- [ ] DQN