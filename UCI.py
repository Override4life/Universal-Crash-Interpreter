import re
import os
import sys
import platform

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# ---------------------------------------------------------
# Beginner-Friendly Crash Log Interpreter
# Copyright (c) 2026 Bjorn Jonker
# License: CC BY-NC-ND 4.0 (Use allowed, No Modifications)
# ---------------------------------------------------------

console = Console()

# --- THE MULTILINGUAL BRAIN ---
LANG_DATA = {
    "python": {
        "name": "Python",
        "color": "blue",
        "translations": {
            "NameError": "🔍 Unknown variable! You're using a name Python doesn't recognize. Check your spelling.",
            "TypeError": "🚫 Data type mismatch! You're trying to do something with the wrong type of data (like adding a string to a number).",
            "IndexError": "🔢 List index out of range! You're asking for an item that isn't there.",
            "KeyError": "🔑 Dictionary key missing! You're looking for a label inside a data object that doesn't exist.",
            "IndentationError": "📐 Spacing error! Python needs your tabs/spaces to be perfectly aligned."
        }
    },
    "javascript": {
        "name": "JavaScript (Node.js)",
        "color": "yellow",
        "translations": {
            "ReferenceError": "🌐 JS doesn't know this variable! Did you forget to declare it with 'let' or 'const'?",
            "TypeError": "🚫 Not a function/object! You're likely trying to use 'null' or 'undefined' as if it were real data.",
            "SyntaxError": "✍️ Typo alert! Check for missing curly braces {} or parentheses ().",
            "RangeError": "📏 Out of range! A number is too big or a list is the wrong size."
        }
    },
    "php": {
        "name": "PHP",
        "color": "magenta",
        "translations": {
            "Parse error": "🐘 PHP Syntax error! Usually a missing semicolon (;) or a bracket.",
            "Fatal error": "💀 The script crashed completely. Often a missing file or a memory limit.",
            "Warning": "⚠️ Something is wrong, but the script kept running. Usually a missing 'include' file.",
            "Notice": "📝 Minor issue. You might be using a variable that hasn't been set yet."
        }
    }
}


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

    # 1. Improved Regex for Steps (Traceback)
    # This now looks for BOTH:
    # - File "path", line 10 (Python/PHP)
    # - at path:10:5 (JavaScript)
    steps = re.findall(r'(?:File "([^"]+)", line (\d+)|at (?:async )?(.+?):(\d+)(?::\d+)?)', content)

    # Clean up the steps (regex findall with multiple groups creates empty strings)
    cleaned_steps = []
    for s in steps:
        # If Python style, s[0] and s[1] are filled. If JS, s[2] and s[3] are filled.
        f_path = s[0] or s[2]
        l_num = s[1] or s[3]
        cleaned_steps.append((f_path.strip(), l_num))

    # 2. Get the specific crash site (the very first step in a JS log or last in Python)
    if cleaned_steps:
        # In JS, the error usually starts at the TOP of the stack.
        # In Python, it's at the BOTTOM.
        target_file, line = cleaned_steps[0] if lang == "javascript" else cleaned_steps[-1]
    else:
        target_file, line = None, "???"

    # 3. Extract Error Type & Description
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
            # We now get 'steps' back from our parse_log function
            lang, line, e_type, e_desc, target_file, steps = parse_log(log_path)

            lang_info = LANG_DATA.get(lang)
            friendly_msg = lang_info["translations"].get(e_type,"I recognize the language, but this specific error is new to my database.")

            # 1. Main Analysis Panel
            analysis = (
                f"[bold yellow]Language:[/bold yellow] {lang_info['name']}\n"
                f"[bold cyan]Crash Site:[/bold cyan] Line {line}\n"
                f"[bold red]Technical:[/bold red] {e_type}: {e_desc}\n"
                f"---"
                f"\n[bold green]EXPLANATION:[/bold green]\n{friendly_msg}"
            )
            console.print(Panel(analysis, title=f"Analysis: {os.path.basename(log_path)}", border_style=lang_info['color']))

            # 2. The "Path to Destruction" (Traceback)
            if steps and len(steps) > 1:
                console.print("\n[bold]🛠️ Traceback (Path leading to the crash):[/bold]")
                for i, (f_path, l_num) in enumerate(steps):
                    # We highlight files that look like your personal projects
                    is_user_file = "Users" in f_path or "Documents" in f_path or "/" in f_path
                    style = "bold green" if is_user_file else "dim"
                    console.print(f"  {i + 1}. [{style}]{os.path.basename(f_path)}[/] at line {l_num}")

            # 3. Code Snippet Preview
            snippet = get_code_snippet(target_file, line)
            if snippet:
                console.print(f"\n[bold]📍 The broken line in {os.path.basename(target_file)}:[/bold]")
                syntax = Syntax(snippet, lang, theme="monokai", line_numbers=False)
                console.print(Panel(syntax, border_style="white", padding=(0, 1)))

            # 4. Final Suggestion
            suggestion = lang_info.get("suggestions", {}).get(e_type)
            if suggestion:
                console.print(f"\n[bold blue]💡 Pro-Tip:[/bold blue] {suggestion}")

        except FileNotFoundError:
            console.print("[red]❌ File not found. Please check the path.[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error during analysis: {e}[/red]")

if __name__ == "__main__":
    main()