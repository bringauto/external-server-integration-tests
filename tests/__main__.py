import os
import sys
import unittest



TEST_DIR_NAME = "tests"


def _run_tests(show_test_names: bool = True) -> None:
    possible_paths = [os.path.join(TEST_DIR_NAME, path) for path in sys.argv[1:]]
    if not possible_paths:
        paths = [TEST_DIR_NAME]
    else:
        paths = []
        for path in possible_paths:
            if os.path.exists(path):
                paths.append(path)
            else:
                print(f"Path '{path}' does not exist. Skipping.")
    suite = unittest.TestSuite()
    for path in paths:
        if os.path.isfile(path):
            file_name = os.path.basename(path)
            if file_name.endswith(".py"):
                pattern, dir = file_name, os.path.dirname(path)
        else:
            pattern, dir = "test_*.py", path
        suite.addTests(unittest.TestLoader().discover(dir, pattern=pattern))
    verbosity = 2 if show_test_names else 1
    unittest.TextTestRunner(verbosity=verbosity, buffer=True).run(suite)


if __name__ == "__main__":
    _run_tests()
