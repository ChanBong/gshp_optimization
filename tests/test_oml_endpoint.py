# Test to check the hgs endpoint

import requests
import json
import os
import pytest

def test_oml_endpoint():
    """
    Test to check the hgs endpoint
    """
    url = "http://localhost:9876/optimise/static"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    """
    sample data
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
    """
    data = {
        "instance_name": "instances/toy_instance.txt",
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
        pytest.fail("The endpoint is not working. Did you start the server?")
    
    assert response.status_code == 200
    print(response.json())
    assert response.json() == {'cost': '41777', 'number_of_riders': '3', 'routes': [[0, 1, 2, 11, 10, 9, 0], [0, 5, 7, 8, 6, 4, 0], [0, 3, 0]]}