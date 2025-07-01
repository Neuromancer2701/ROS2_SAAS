# Copyright 2023 Your Name
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_flake8.main import main_with_errors
import pytest
import os

# It's good practice to define the paths to check explicitly.
# This often includes the main package directory and the test directory.
paths_to_check = [
    'ros2_debug_dashboard', # The main Python package directory
    'test'                  # The test directory itself
]

@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    # Filter out paths that don't exist to prevent errors
    existing_paths = [path for path in paths_to_check if os.path.exists(path)]
    if not existing_paths:
        # If no paths are found (e.g., if script is run from a different context),
        # this test might pass vacuously or fail depending on how main_with_errors handles empty argv.
        # It's better to be explicit.
        print("Warning: No valid paths found for flake8 check. Test might not be effective.")
        # Depending on strictness, you might want to assert False here or handle it.
        # For now, let it proceed; main_with_errors might handle it or default to '.'

    rc, errors = main_with_errors(argv=existing_paths if existing_paths else ['.']) # Default to '.' if no paths specified
    assert rc == 0, \
        'Found %d code style errors / warnings:\n' % len(errors) + \
        '\n'.join(errors)
