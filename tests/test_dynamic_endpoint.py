# Test to check the hgs endpoint

import requests
import json
import pytest

def test_oml_endpoint():
    """
    Test to check the hgs endpoint
    """
    url = "http://localhost:9876/optimise/dynamic"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    """
    sample data
    {
    pickup_instance: "name_of_the_pickup_instance",
    delivery_instance: "name_of_the_delivery_instance",
    delivery_vrptw_instance: "name_of_the_delivery_vrptw_instance",
    solution_instance: "name_of_the_solution_instance",
    pickup_folder: "name_of_the_pickup_folder",
    delivery_cache: "name_of_the_delivery_cache",
    pickup_cache: "name_of_the_pickup_cache",
    hindsight: "boolean_value_wheater_we_want_to_solve_hindsight_or_not"
    }
    """
    data = {
        "pickup_instance": "bangalore_pickups",
        "delivery_instance": "bangalore dispatch address",
        "delivery_vrptw_instance": "instances/instance_time_18000_bangalore dispatch address.txt",
        "solution_instance": "sols/instance_time_18000_bangalore dispatch address-11-05-50-05.json",
        "pickup_folder": "pickup",
        "delivery_cache": True,
        "pickup_cache": False,
        "hindsight": False, 
        "method": "local_search"
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
    except:
        pytest.fail("The endpoint is not working. Did you start the server?")
    
    assert response.status_code == 200
    print(response.json())
    assert response.json() == {'cost': '41777', 'number_of_riders': '3', 'routes': [[0, 1, 2, 11, 10, 9, 0], [0, 5, 7, 8, 6, 4, 0], [0, 3, 0]]}