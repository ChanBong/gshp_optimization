
from acg import generate_instance
import argparse

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--delivery_instance")
    parser.add_argument("--use_cache", action="store_false")
    return parser.parse_args()

def main():
    args = parse_args()
    generate_instance(args.delivery_instance, args.use_cache)
    print("Done")

if __name__ == "__main__":
    main()