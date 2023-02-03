import argparse
import cProfile
import pstats
import sys
from datetime import datetime

import tools
from environment import ControllerEnvironment, VRPEnvironment
from strategies import solve_dynamic, solve_hindsight
from strategies.config import Config
from tools import add_depot_to_solution, clean_costs_and_solution


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--instance")
    parser.add_argument("--instance_seed", type=int, default=1)
    parser.add_argument("--solver_seed", type=int, default=1)
    parser.add_argument("--epoch_tlim", type=int, default=120)
    parser.add_argument("--config_loc", default="configs/solver.toml")
    parser.add_argument("--profile", action="store_true")

    problem_type = parser.add_mutually_exclusive_group()
    problem_type.add_argument("--static", action="store_false")
    problem_type.add_argument("--hindsight", action="store_true")

    return parser.parse_args()

def process_cost_and_routes(costs, routes):
    costs, routes = clean_costs_and_solution(costs, routes)
    routes = sorted(routes, key=lambda x: (-len(x), x[0]))
    routes = add_depot_to_solution(routes)
    number_of_riders = len(routes)

    return costs, routes, number_of_riders

def run(args):
    print(type(args))
    if args.instance is not None:
        env = VRPEnvironment(
            seed=args.instance_seed,
            instance=tools.read_vrplib(args.instance),
            epoch_tlim=args.epoch_tlim,
            is_static=args.static,
        )
        print("Instance loaded")
    else:
        # Run within external controller
        assert not args.hindsight, "Cannot solve hindsight using controller"
        env = ControllerEnvironment(sys.stdin, sys.stdout)

    name_of_instance = args.instance.split("/")[-1].split(".")[0]

    # Make sure these parameters are not used by your solver
    args.instance = None
    args.instance_seed = None
    args.static = None
    args.epoch_tlim = None

    config = Config.from_file(args.config_loc)

    if args.hindsight:
        solve_hindsight(env, config.static(), args.solver_seed)
    else:
        costs, routes = solve_dynamic(env, config, args.solver_seed)

        costs, routes, number_of_riders = process_cost_and_routes(costs, routes)
        tools.write_solution(f"solutions/{name_of_instance}.json", costs, routes, number_of_riders)
    
        print(f"Costs: {costs}\n")
        print(f"Routes: {routes}\n")
        print(f"Number of riders: {number_of_riders}\n")
    
        return costs, routes, number_of_riders

def oml_solver(instance_dict):
    '''
    this function is used to solve the problem using the oml endpoint
    convert a dictionary to a args namespace and then call the run function and return the costs and solution
    '''
    args = argparse.Namespace()
    args.instance = instance_dict['instance_name']
    args.instance_seed = instance_dict['instance_seed']
    args.solver_seed = instance_dict['solver_seed']
    args.epoch_tlim = instance_dict['epoch_tlim']
    args.config_loc = instance_dict['config_loc']
    args.profile = instance_dict['profile']
    args.static = instance_dict['static']
    args.hindsight = instance_dict['hindsight']

    costs, solution, number_of_riders = run(args)
    return costs, solution, number_of_riders

def main():
    args = parse_args()
    print(args)
    if args.profile:
        print("HERE_BEFORE")
        with cProfile.Profile() as profiler:
            run(args)
        print("HERE")
        stats = pstats.Stats(profiler).strip_dirs().sort_stats("time")
        stats.print_stats()

        now = datetime.now().isoformat()
        stats.dump_stats(f"logs/log-{now}.pstat")
    else:
        run(args)


if __name__ == "__main__":
    main()
