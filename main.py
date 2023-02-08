
from acg import generate_instance, fetch_delivery_from_api
import argparse
import requests
import json

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--delivery_instance")
    parser.add_argument("--use_cache", action="store_false")
    return parser.parse_args()

def test_oml_endpoint(file_name):
    """
    Test to check the hgs endpoint
    """
    url = "http://localhost:9876/optimise/static"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    data = {
        "instance_name": f"{file_name}",
        "instance_seed": 1,
        "solver_seed": 1,
        "epoch_tlim": 5,
        "config_loc": "configs/solver.toml",
        "profile": True,
        "static": True,
        "hindsight": False
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
    except:
        print("The endpoint is not working. Did you start the server?")
        exit(0)

    # keep adding response.json to a file
    with open("results.txt", "a") as f:
        f.write(str(response.json()))
        f.write("\n")

    print(response.json(), file_name)

def tune_params():
    for i in range(1000, 100000, 1000):
        instance_file = generate_instance('bangalore dispatch address', use_cache=True, one_day_time=i)
        print(instance_file)
        print("Testing for one day time : ", i)
        try:
            test_oml_endpoint(instance_file)
        except:
            print("Error in testing for one day time : ", i)


def main():
    args = parse_args()
    tune_params()
    print("Done")


if __name__ == "__main__":
    main()