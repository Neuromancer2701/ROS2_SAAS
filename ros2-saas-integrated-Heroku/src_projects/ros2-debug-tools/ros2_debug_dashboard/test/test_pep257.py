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

from ament_pep257.main import main
import pytest
import os

# It's good practice to define the paths to check explicitly.
paths_to_check = [
    'ros2_debug_dashboard', # The main Python package directory
    'test'                  # The test directory itself
    # Add other relevant Python files or directories if necessary
    # e.g., 'setup.py' if you want to check it, though often linters focus on package code.
]

@pytest.mark.pep257
@pytest.mark.linter
def test_pep257():
    # Filter out paths that don't exist
    existing_paths = [path for path in paths_to_check if os.path.exists(path)]
    if not existing_paths:
        print("Warning: No valid paths found for pep257 check. Test might not be effective.")

    rc = main(argv=existing_paths if existing_paths else ['.']) # Default to '.'
    assert rc == 0, 'Found docstring style errors'
