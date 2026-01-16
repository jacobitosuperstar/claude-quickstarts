from typing import List, Dict, Any
import os
import json
from fastapi.testclient import TestClient
from httpx import Response
from main import app
from app.settings import settings


current_path: str = os.path.dirname(os.path.abspath(__file__))
test_cases_folder: str = os.path.join(current_path, "tests")


def json_test_cases(folder_path:str) -> List[Dict]:
    """Takes all the json files from the tests folder and picks up the test
    cases from them, creating a list with each one of the test cases.
    each test case will have:
        url, description, input, expected_output
    """
    json_files: List = []
    test_cases: List = []
    # getting all the json files from the test folder
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            json_files.append(os.path.join(folder_path, file))
    # looping over each json file to pick up the test cases
    for json_file in json_files:
        with open(json_file, mode='r', encoding='UTF-8') as file:
            test_cases_file: Dict[str, Any] = json.load(file)
        # appending the test cases into the test_cases list
        for test_case in test_cases_file["test_cases"]:
            test_cases.append(
                (
                    test_cases_file["url"],
                    test_case["test_description"],
                    test_case["input"],
                    test_case["expected_output"],
                )
            )
    return test_cases

test_cases: List[Dict] = json_test_cases(test_cases_folder)

# Force disable authentication for tests
settings.disable_auth = True

client: TestClient = TestClient(app)


def pytest_generate_tests(metafunc):
    if "input" in metafunc.fixturenames:
        metafunc.parametrize('url, test_description, input, expected_output', test_cases)


def test_server(url, test_description, input, expected_output):
    _: Any = input
    response: Response = client.get(
        url,
    )
    assert response.status_code == expected_output["status_code"], (
        f"Expected {expected_output["status_code"]}, "
        f"but got {response.status_code} in the test case {test_description}"
    )
