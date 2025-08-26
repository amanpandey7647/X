# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                   XClient Framework - Python Upgrader for macOS
#
#   This script automates the process of upgrading Python to the latest stable
#   version on macOS using the Homebrew package manager.
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
import shutil

def run_command(command: str) -> int:
    """
    Executes a shell command using os.system and returns the exit code.
    This provides a clear entry point for all system calls.
    
    Args:
        command (str): The command to execute.

    Returns:
        int: The exit code of the command (0 for success).
    """
    print(f"\n[EXEC] Running command: {command}")
    print("-" * 70)
    exit_code = os.system(command)
    print("-" * 70)
    return exit_code

def check_environment():
    """
    Performs critical pre-flight checks to ensure the script can run safely.
    """
    # 1. Check for macOS
    if sys.platform != 'darwin':
        print("[ERROR] This script is designed exclusively for macOS. Aborting.")
        sys.exit(1)
        
    # 2. Check for Homebrew
    if not shutil.which('brew'):
        print("[ERROR] Homebrew is not installed. Homebrew is required to safely manage Python versions.")
        print("Please install it by running the following command in your terminal, then run this script again:")
        print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
        sys.exit(1)
        
    print("[SUCCESS] Environment checks passed. Homebrew is installed.")

def upgrade_python():
    """
    Handles the main logic for updating Homebrew and installing the latest Python.
    """
    print("\n--- Step 1: Updating Homebrew ---")
    print("This will ensure all package formulae are up-to-date.")
    if run_command("brew update") != 0:
        print("[ERROR] Failed to update Homebrew. Please check your internet connection and try again.")
        sys.exit(1)
    print("[SUCCESS] Homebrew updated successfully.")
    
    print("\n--- Step 2: Installing/Upgrading Python ---")
    print("Homebrew will now install the latest stable version of Python 3. This may take some time.")
    if run_command("brew install python") != 0:
        print("[ERROR] Failed to install Python via Homebrew. Please check the output above for errors.")
        sys.exit(1)
    print("[SUCCESS] Python has been successfully installed/upgraded via Homebrew.")

def print_final_instructions():
    """
    Prints the final, mandatory manual steps for the user to complete the setup.
    """
    # Determine the user's shell to provide the correct instructions.
    shell_path = os.getenv("SHELL", "")
    if "zsh" in shell_path:
        config_file = "~/.zshrc"
    elif "bash" in shell_path:
        config_file = "~/.bash_profile"
    else:
        config_file = "your shell's configuration file (e.g., ~/.zshrc or ~/.bash_profile)"

    print("\n" + "=" * 70)
    print("          >>> ACTION REQUIRED: FINAL CONFIGURATION STEPS <<<")
    print("=" * 70)
    print("\nPython has been installed, but you must now tell your system to use it.")
    print("This final step must be done manually to ensure your system's stability.")
    
    print(f"\n1. Open your shell configuration file by running this command:")
    print(f"   open {config_file}")
    
    print(f"\n2. Add the following line to the VERY TOP of the file. This is crucial.")
    print("   This ensures that the Homebrew version of Python is found first.")
    print("\n   COPY THIS LINE:")
    print('   export PATH="/opt/homebrew/bin:$PATH"')
    
    print(f"\n3. Save the file and completely CLOSE your terminal window.")
    
    print(f"\n4. Open a NEW terminal window and verify the installation by running:")
    print("   python3 --version")
    
    print("\n   The output should now show a version of 3.10 or higher (e.g., Python 3.12.3).")
    print("   If it does, the upgrade was successful!")
    print("\n   You can now proceed to install the XClient Framework dependencies.")
    print("=" * 70)

def main():
    """
    The main function to orchestrate the entire upgrade process.
    """
    check_environment()
    upgrade_python()
    print_final_instructions()

if __name__ == "__main__":
    # This block ensures the code only runs when the script is executed directly.
    main()