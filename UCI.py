import re
import os
import sys
import platform
import json

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
    print("1. Use UCI-v1.0")
    print("2. Clear Screen")
    print("3. Exit")

def main():

    print_header()
    while True:
        print_menu()
        choice = input("\n Enter your choice: ")

        if choice == "1":
            log_path = input("\n Enter path to log file: ").strip()
        elif choice == "2":
            clear_screen()
            print_header()
            continue
        elif choice == "3":
            sys.exit()
        else:
            print("\nInvalid choice. Please try again.")

        try:
            lang, line, e_type, e_desc, target_file, steps = parse_log(log_path)

            lang_info = LANG_DATA.get(lang)
            error_info = lang_info["translations"].get(e_type, "This is a custom or rare error. Check the technical details above to see what specifically went wrong!")

            if isinstance(error_info, dict):
                explanation_text = (
                    f"[bold green]WHAT HAPPENED:[/bold green]\n{error_info.get('desc')}\n\n"
                    f"[bold blue]HOW TO FIX IT:[/bold blue]\n{error_info.get('fix')}"
                )
            else:
                msg = error_info if error_info else "I don't have a specific explanation for this error yet."
                explanation_text = f"[bold green]EXPLANATION:[/bold green]\n{msg}"

            # Main Analysis Panel
            analysis = (
                f"[bold yellow]Language:[/bold yellow] {lang_info['name']}\n"
                f"[bold cyan]Crash Site:[/bold cyan] Line {line}\n"
                f"[bold red]Technical:[/bold red] {e_type}: {e_desc}\n"
                f"---"
                f"\n{explanation_text}"
            )
            console.print(Panel(analysis, title=f"Analysis: {os.path.basename(log_path)}", border_style=lang_info['color']))

            # The "Path to Destruction" (Smart Slicer)
            if steps:
                console.print("\n[bold]🛠️ Traceback (Path leading to the crash):[/bold]")

                if len(steps) > 10:
                    f_path, l_num = steps[0]
                    console.print(f"  1. [dim]{os.path.basename(f_path)}[/] at line {l_num}")

                    console.print(
                        f"     [bold yellow]... {len(steps) - 6} internal library steps hidden ...[/bold yellow]")

                    for i, (f_path, l_num) in enumerate(steps[-5:], start=len(steps) - 4):
                        is_user_file = "views.py" in f_path or "/" in f_path
                        style = "bold green" if is_user_file else "dim"
                        console.print(f"  {i}. [{style}]{os.path.basename(f_path)}[/] at line {l_num}")
                else:
                    for i, (f_path, l_num) in enumerate(steps, 1):
                        console.print(f"  {i}. [bold green]{os.path.basename(f_path)}[/] at line {l_num}")

            # Code Snippet Preview
            snippet = get_code_snippet(target_file, line)
            if snippet:
                console.print(f"\n[bold]📍 The broken line in {os.path.basename(target_file)}:[/bold]")
                syntax = Syntax(snippet, lang, theme="monokai", line_numbers=False)
                console.print(Panel(syntax, border_style="white", padding=(0, 1)))

            # Final Suggestion
            suggestion = lang_info.get("suggestions", {}).get(e_type)
            if suggestion:
                console.print(f"\n[bold blue]💡 Pro-Tip:[/bold blue] {suggestion}")

        except FileNotFoundError:
            console.print("[red]❌ File not found. Please check the path.[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error during analysis: {e}[/red]")

if __name__ == "__main__":
    main()