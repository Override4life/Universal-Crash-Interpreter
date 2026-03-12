import re
import os
import sys
import platform
import json
import time
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# ---------------------------------------------------------
# Beginner-Friendly Crash Log Interpreter
# Copyright (c) 2026 Bjorn Jonker
# License: CC BY-NC-ND 4.0 (Use allowed, No Modifications)
# ---------------------------------------------------------

console = Console()

def load_translations():
    # Path to your translation file
    file_path = "translations.json"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Fallback if the file is missing
        print("⚠️ Warning: translations.json not found!")
        return {}

# --- THE MULTILINGUAL BRAIN ---
LANG_DATA = load_translations()

# Runner Mode
def run_and_catch(script_path):
    """The Runner: Executes your code. Returns True if it crashed, False otherwise."""
    console.print(f"[bold yellow]🚀 Launching {os.path.basename(script_path)}...[/bold yellow]\n")

    ext = os.path.splitext(script_path)[1]
    cmd = ["python", script_path] if ext == ".py" else ["node", script_path] if ext == ".js" else ["php", script_path]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    stdout, stderr = process.communicate()

    if stdout:
        print(stdout)

    if stderr:
        console.print("\n[bold reverse red] 💥 CRASH DETECTED [/bold reverse red]")

        with open("temp_crash.log", "w", encoding="utf-8") as f:
            f.write(stderr)

        lang, line, e_type, e_desc, target_file, steps = parse_log("temp_crash.log")
        display_analysis(script_path, lang, line, e_type, e_desc, target_file, steps)

        if os.path.exists("temp_crash.log"):
            os.remove("temp_crash.log")
        return True  # Add this: Signal that it crashed
    else:
        console.print("\n[bold green]Script finished successfully with no errors![/bold green]")
        return False  # Add this: Signal that it worked


# Live Monitor
def display_analysis(log_path, lang, line, e_type, e_desc, target_file, steps):
    """The Renderer: This is the unified engine for showing results."""
    lang_info = LANG_DATA.get(lang)
    error_info = lang_info["translations"].get(e_type, "This is a custom or rare error.")

    # 1. Format Explanation
    if isinstance(error_info, dict):
        explanation_text = (
            f"[bold green]WHAT HAPPENED:[/bold green]\n{error_info.get('desc')}\n\n"
            f"[bold blue]HOW TO FIX IT:[/bold blue]\n{error_info.get('fix')}"
        )
    else:
        explanation_text = f"[bold green]EXPLANATION:[/bold green]\n{error_info}"

    # 2. Main Panel
    analysis = (
        f"[bold yellow]Language:[/bold yellow] {lang_info['name']}\n"
        f"[bold cyan]Crash Site:[/bold cyan] Line {line}\n"
        f"[bold red]Technical:[/bold red] {e_type}: {e_desc}\n"
        f"---"
        f"\n{explanation_text}"
    )
    console.print(Panel(analysis, title=f"Analysis: {os.path.basename(log_path)}", border_style=lang_info['color']))

    # 3. Traceback Slicer
    if steps:
        console.print("\n[bold]🛠️ Traceback (Path leading to the crash):[/bold]")
        if len(steps) > 10:
            f1, l1 = steps[0]
            console.print(f"  1. [dim]{os.path.basename(f1)}[/] at line {l1}")
            console.print(f"     [bold yellow]... {len(steps) - 6} internal library steps hidden ...[/bold yellow]")
            for i, (f_path, l_num) in enumerate(steps[-5:], start=len(steps) - 4):
                style = "bold green" if "views.py" in f_path or "/" in f_path else "dim"
                console.print(f"  {i}. [{style}]{os.path.basename(f_path)}[/] at line {l_num}")
        else:
            for i, (f_path, l_num) in enumerate(steps, 1):
                console.print(f"  {i}. [bold green]{os.path.basename(f_path)}[/] at line {l_num}")

    # 4. Code Snippet
    snippet = get_code_snippet(target_file, line)
    if snippet:
        console.print(f"\n[bold]📍 The broken line in {os.path.basename(target_file)}:[/bold]")
        syntax = Syntax(snippet, lang, theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="white", padding=(0, 1)))

def process_live_error(raw_text, log_path):
    """Processes new lines and sends them to the display engine."""
    lang, line, e_type, e_desc, target_file, steps = parse_log(log_path)

    # Call the unified display
    display_analysis(log_path, lang, line, e_type, e_desc, target_file, steps)

def detect_language(content):
    """The Detective: Identifies the language based on clues inside the text."""
    content_lower = content.lower()
    if "traceback" in content_lower or ".py" in content_lower:
        return "python"
    if "fatal error" in content_lower or "parse error" in content_lower or ".php" in content_lower:
        return "php"
    if "referenceerror" in content_lower or "at object." in content_lower or ".js" in content_lower:
        return "javascript"
    return "python"  # Default fallback


def parse_log(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lang = detect_language(content)

    #Traceback
    steps = re.findall(r'(?:File "([^"]+)", line (\d+)|at (?:async )?(.+?):(\d+)(?::\d+)?)', content)

    # Clean up the steps (regex findall with multiple groups creates empty strings)
    cleaned_steps = []
    for s in steps:
        f_path = s[0] or s[2]
        l_num = s[1] or s[3]
        cleaned_steps.append((f_path.strip(), l_num))

    # Get the specific crash site (the very first step in a JS log or last in Python)
    if cleaned_steps:
        target_file, line = cleaned_steps[0] if lang == "javascript" else cleaned_steps[-1]
    else:
        target_file, line = None, "???"

    # Extract Error Type & Description
    error_match = re.search(r"(\w+(?:\s?error|Exception|Error)):? (.+)", content, re.IGNORECASE)
    e_type = error_match.group(1) if error_match else "Unknown Error"
    e_desc = error_match.group(2) if error_match else "No description."

    return lang, line, e_type, e_desc, target_file, cleaned_steps


def get_code_snippet(file_path, line_num):
    """Optional: Reads the actual broken file to show the line of code."""
    try:
        if file_path and os.path.exists(file_path.strip()):
            with open(file_path.strip(), 'r') as f:
                lines = f.readlines()
                return lines[int(line_num) - 1].strip()
    except:
        return None
    return None

def clear_screen():
    command = "cls" if platform.system().lower() == "windows" else "clear"
    os.system(command)


def print_header():
    header_text = (
        "[bold magenta]Universal Crash Interpreter v1.0[/bold magenta]\n"
        "[dim]Debugging: Python, JS, & PHP | Mode: Deep Analysis[/dim]\n\n"
        "[dim]Copyright (c) 2026 Bjorn Jonker[/dim]\n"
        "[dim]License: CC BY-NC-ND 4.0 (Use allowed, No Modifications)[/dim]"
    )

    console.print(Panel(header_text, expand=False))

# Menu
def print_menu():
    print("\nMenu:")
    print("1. Analyze Static Log")
    print("2. Runner Mode (Run your script through UCI)") # New!
    print("3. Clear Screen")
    print("4. Exit")


def main():
    clear_screen()
    print_header()

    # This variable "remembers" your current project script
    active_script = ""

    while True:
        print_menu()
        choice = input("\n Enter choice: ").strip()

        # OPTION 1: Manual Analysis (for old logs)
        if choice == "1":
            log_path = input(" Path to log file: ").strip()
            if os.path.exists(log_path):
                try:
                    lang, line, e_type, e_desc, target_file, steps = parse_log(log_path)
                    display_analysis(log_path, lang, line, e_type, e_desc, target_file, steps)
                except Exception as e:
                    console.print(f"[red]❌ Analysis failed: {e}[/red]")
            else:
                console.print("[red]❌ File not found.[/red]")

        # OPTION 2: The New Runner Mode
        elif choice == "2":
            if not active_script:
                active_script = console.input(" Which script are you editing? (e.g. main.py): ").strip()

            if os.path.exists(active_script):
                 while True:
                    clear_screen()
                    print_header()

                    # Run and capture the result
                    did_crash = run_and_catch(active_script)

                    if not did_crash:
                        # SUCCESS: Clear the memory so it doesn't auto-run next time
                        active_script = ""
                        console.print("\n[dim]Returning to menu...[/dim]")
                        time.sleep(2)
                        break  # Exit the loop and go back to main menu
                    else:
                        # CRASHED: Keep the script in memory so we can RETRY
                        print(f"\n[dim]Currently editing: {active_script}[/dim]")
                        action = console.input("\n[bold cyan]Press Enter to RETRY[/bold cyan] or [bold yellow]'m'[/bold yellow] for Menu: ").lower()
                        if action == 'm':
                            break
            else:
                console.print(f"[red]❌ {active_script} not found![/red]")
                active_script = ""

        # OPTION 3: UI Housekeeping
        elif choice == "3":
            clear_screen()
            print_header()

        # OPTION 4: Exit
        elif choice == "4":
            console.print("[bold magenta]Happy coding, Goodbye.[/bold magenta]")
            sys.exit()

        else:
            console.print("[yellow]⚠Invalid choice. Try again.[/yellow]")

if __name__ == "__main__":
    main()