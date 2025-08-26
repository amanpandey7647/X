# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#               XClient Framework - Dependency Installer Script
#
#   This script will install all necessary dependencies for the XClient Framework
#   using the correct Python interpreter. It is designed to be run directly.
#
#   Copyright (C) 2025-2026 Aman Pandey. All Rights Reserved.
#
#   This file is part of the XClient Framework. It is proprietary and confidential.
#   Unauthorised copying, modification, distribution, or use of this file,
#   via any medium, is strictly prohibited without the express written
#   permission of the copyright holder.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os
import sys

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
# Define all the packages that need to be installed.

# This is the special URL for the Telethon v2 development branch from the PDF.
# The #subdirectory=client part is crucial.
TELETHON_V2_URL = "https://github.com/LonamiWebs/Telethon/archive/v2.zip#subdirectory=client"

# A list of other required dependencies for our framework.
OTHER_DEPENDENCIES = [
    "pymongo",
    "requests",
    "redis",
    "setuptools" # For the advanced database backend
]

# ==============================================================================
#  INSTALLATION LOGIC
# ==============================================================================

def install_dependencies():
    """
    This function will construct and execute the command to install all framework
    dependencies using the os.system call.
    """
    print("--- XClient Framework Dependency Installer ---")

    # --- Step 1: Determine the correct Python executable ---
    # This is the most important step. sys.executable gives the full path to the
    # Python interpreter that is currently running this script. This ensures
    # we use the correct 'pip' and avoid any system path issues.
    python_executable = sys.executable
    print(f"\n[INFO] Using Python interpreter: {python_executable}")

    # --- Step 2: Construct the full pip command ---
    # We will build the command programmatically for clarity and robustness.
    # Using 'python -m pip' is the recommended way to call pip.
    
    # We will use --upgrade to ensure we get the latest compatible versions.
    base_command = f'"{python_executable}" -m pip install --upgrade'
    
    # Join all other dependencies into a single string.
    dependencies_str = " ".join(OTHER_DEPENDENCIES)
    
    # Combine everything into the final command.
    # The URL is quoted to handle special characters like '#'.
    final_command = f'{base_command} {dependencies_str} "{TELETHON_V2_URL}"'

    print("\n[INFO] The following command will be executed:")
    print("=" * 70)
    print(final_command)
    print("=" * 70)
    print("\n[INFO] Starting installation... This may take a few moments.")

    # --- Step 3: Execute the command using os.system ---
    # os.system will run the command in a subshell.
    # It returns an exit code. '0' means success, anything else means failure.
    exit_code = os.system(final_command)

    # --- Step 4: Check the result ---
    # We must check the exit code to confirm if the installation was successful.
    print("\n--- Installation Result ---")
    if exit_code == 0:
        print("\n[SUCCESS] All dependencies for the XClient Framework have been installed successfully!")
        print("You can now run the main.py file.")
    else:
        print(f"\n[ERROR] The installation failed with exit code: {exit_code}.")
        print("This is likely not a problem with the script, but with your environment.")
        print("\nPlease check the following:")
        print("  1. Ensure your Python version is 3.10 or newer (`python3 --version`).")
        print("  2. Make sure you have an active internet connection.")
        print("  3. You might be missing necessary build tools (like 'wheel' or a C compiler). Try running: `pip install --upgrade pip wheel setuptools`")

# ==============================================================================
#  SCRIPT ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # This block ensures the code only runs when the script is executed directly.
    install_dependencies()
