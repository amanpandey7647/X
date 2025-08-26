# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#                    Command Execution Utility Script
#
#   This script demonstrates the correct and modern ways to execute
#   shell commands from within a Python program using the 'os' and
#   'subprocess' modules.
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
import subprocess
import sys

# ==============================================================================
#  METHOD 1: THE SIMPLE `os.system` APPROACH
# ==============================================================================

def run_simple_os_commands():
    """
    Demonstrates the basic os.system() method.

    This method is very straightforward. It simply passes the command string to
    your system's shell. However, it is limited because you cannot capture the
    output of the command in a variable. It is generally recommended to use the
    'subprocess' module for more serious work.
    """
    print("--- Method 1: Using os.system() (Simple but Limited) ---")

    # Example 1: Listing files in the current directory.
    # The output will be printed directly to your console, just like in a terminal.
    print("\n[INFO] Running 'ls -l' command...")
    
    # On Windows, you would use 'dir' instead of 'ls -l'
    list_command = "ls -l" if sys.platform != "win32" else "dir"
    os.system(list_command)

    # Example 2: Pinging a server a few times.
    print("\n[INFO] Running 'ping -c 3 google.com' command...")
    ping_command = "ping -c 3 google.com"  # The '-c 3' sends only 3 packets.
    if sys.platform == "win32":
        ping_command = "ping -n 3 google.com" # Windows uses '-n' for count.
    
    os.system(ping_command)
    print("\n[SUCCESS] os.system() examples finished.")


# ==============================================================================
#  METHOD 2: THE ADVANCED `subprocess.run` APPROACH
# ==============================================================================

def run_advanced_subprocess_commands():
    """
    Demonstrates the modern and recommended subprocess.run() method.

    This method is much more powerful and secure. It allows you to:
    1.  Pass commands as a list, which prevents security issues (shell injection).
    2.  Capture the command's output (stdout) and errors (stderr).
    3.  Check if the command was successful and handle errors gracefully.
    """
    print("\n\n--- Method 2: Using subprocess.run() (Advanced and Recommended) ---")

    # --- Example 2a: Running a command and capturing its output ---
    print("\n[INFO] Running 'ls -l' and capturing its output into a variable...")
    
    list_command = ["ls", "-l"] if sys.platform != "win32" else ["dir"]

    try:
        # We run the command and capture the result in a variable.
        result = subprocess.run(
            list_command,
            capture_output=True,  # This is the key to capturing output.
            text=True,            # This decodes the output as a string.
            check=True            # This will raise an error if the command fails.
        )

        print("[SUCCESS] Command executed successfully.")
        print("\n--- CAPTURED OUTPUT ---")
        # The output is now available in the 'stdout' attribute.
        print(result.stdout)
        print("--- END OF CAPTURED OUTPUT ---")

    except FileNotFoundError:
        print(f"[ERROR] The command '{list_command[0]}' was not found on your system.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] The command failed with exit code {e.returncode}.")
        print(f"Error output:\n{e.stderr}")

    # --- Example 2b: Handling a command that fails ---
    print("\n[INFO] Demonstrating error handling by running a failing command...")
    
    failing_command = ["ls", "this_file_does_not_exist_12345.tmp"]

    try:
        subprocess.run(failing_command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # The 'check=True' argument makes it easy to catch errors like this.
        print("[SUCCESS] Successfully caught the expected error.")
        print(f"Command failed with exit code: {e.returncode}")
        print(f"Captured standard error stream:\n{e.stderr}")

# ==============================================================================
#  MAIN EXECUTION BLOCK
# ==============================================================================

def main():
    """
    The main function to orchestrate the demonstration.
    """
    run_simple_os_commands()
    run_advanced_subprocess_commands()

if __name__ == "__main__":
    # This block ensures the code only runs when the script is executed directly.
    main()