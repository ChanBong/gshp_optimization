import argparse
import cProfile
import pstats
import sys
from datetime import datetime

import tools
from environment import ControllerEnvironment, VRPEnvironment
from strategies import solve_dynamic, solve_hindsight
from strategies.config import Config


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--instance")
    parser.add_argument("--instance_seed", type=int, default=1)
    parser.add_argument("--solver_seed", type=int, default=1)
    parser.add_argument("--epoch_tlim", type=int, default=120)
    parser.add_argument("--config_loc", default="configs/solver.toml")
    parser.add_argument("--profile", action="store_true")

    problem_type = parser.add_mutually_exclusive_group()
    problem_type.add_argument("--static", action="store_true")
    problem_type.add_argument("--hindsight", action="store_true")

    return parser.parse_args()


def run(args):
    print(args)
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

    store_name_of_instance = args.instance.split("/")[-1]

    # Make sure these parameters are not used by your solver
    args.instance = None
    args.instance_seed = None
    args.static = None
    args.epoch_tlim = None

    config = Config.from_file(args.config_loc)

    if args.hindsight:
        solve_hindsight(env, config.static(), args.solver_seed)
    else:
        print("Solving")
        costs, solution = solve_dynamic(env, config, args.solver_seed)
        print("Solved")
        print(costs)
        print(solution)
        print("#" * 80)
        # Dump costs and solution to file
        with open(f"solutions/{store_name_of_instance}-{args.solver_seed}.txt", "w") as f:
            f.write(f"Costs: {costs}\n")
            f.write(f"Solution: {solution}\n")



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
