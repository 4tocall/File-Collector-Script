import os
import argparse
import subprocess
import platform

IGNORED_DIRECTORIES = { '__pycache__', '.git', '.idea', '.vscode', '__init__', 'build', 'dist', 'venv', 'node_modules', 'env', '.venv', '.mypy_cache', '.pytest_cache', '.vs', '__pycache__', '.ipynb_checkpoints', '.mypy_cache', '.pylint', '.pytest_cache', '.tox', '.serverless', '.local', '.history', '.eggs', '*.egg-info', '*.DS_Store' }

ALLOWED_EXTENSIONS = {'js', 'jsx', 'html', 'json', 'xml', 'yaml', 'yml', 'scss', 'sass', 'css', 'py', 'php'}

ENTER_EXTENSIONS_PROMPT = "Enter file extensions separated by spaces: "
SELECT_INDICES_PROMPT = "Enter the indices of the files you want to collect (separated by spaces), or press Enter for 'all': "

def is_ignored_directory(directory):
    return directory in IGNORED_DIRECTORIES

def is_allowed_extension(extension):
    return extension in ALLOWED_EXTENSIONS

def get_extension(file):
    _, extension = os.path.splitext(file)
    return extension[1:]

def filter_allowed_files(files, extensions):
    return [file for file in files if get_extension(file) in extensions]

def collect_files(extensions):
    collected_files = []
    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if not is_ignored_directory(d)]

        if os.path.basename(root) not in IGNORED_DIRECTORIES:
            collected_files.extend([os.path.join(root, file) for file in filter_allowed_files(files, extensions)])

    return collected_files

def filter_allowed_extensions(extensions):
    return list(filter(lambda ext: ext in ALLOWED_EXTENSIONS, extensions))

def get_possible_extensions():
    extensions_set = set()

    for root, dirs, files in os.walk(".", topdown=True):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]

        if os.path.basename(root) not in IGNORED_DIRECTORIES:
            for file in files:
                _, extension = os.path.splitext(file)
                extensions_set.add(extension[1:])

    return list(filter(lambda ext: ext in ALLOWED_EXTENSIONS, extensions_set))

def display_files(files):
    for i, file in enumerate(files):
        print(f"[{i}] {file}")

def copy_to_clipboard(content):
    system_platform = platform.system()
    
    if system_platform == "Darwin":  # macOS
        subprocess.run(["pbcopy"], input=content.encode("utf-8"))
    elif system_platform == "Linux":
        try:
            subprocess.run(["xclip", "-selection", "clipboard"], input=content.encode("utf-8"))
        except FileNotFoundError:
            print("Command 'xclip' not found. Please install xclip or use a package like pyperclip.")
    elif system_platform == "Windows":
        subprocess.run(["clip"], input=content.encode("utf-8"), shell=True)
    else:
        print("Clipboard copy not supported on this platform. Please use a package like pyperclip.")

def open_file_in_default_app(file_path):
    system_platform = platform.system()

    if system_platform == "Darwin":
        subprocess.run(["open", file_path])
    elif system_platform == "Linux":
        subprocess.run(["xdg-open", file_path])
    elif system_platform == "Windows":
        subprocess.run(["start", "notepad", file_path], shell=True)
    else:
        print("Opening files not supported on this platform.")

def main():
    parser = argparse.ArgumentParser(description='File Collector')
    parser.add_argument('extensions', nargs='*', default=[], choices=list(ALLOWED_EXTENSIONS), help='File extensions to collect')
    parser.add_argument('-extract', action='store_true', help='Extract content')
    parser.add_argument('-all', action='store_true', help='Extract all files')
    parser.add_argument('-open', action='store_true', help='Open the generated file in the default app')
    parser.add_argument('-copy', action='store_true', help='Copy the content to the clipboard')

    args = parser.parse_args()

    extensions = args.extensions
    do_extract = args.extract
    extract_all = args.all
    open_file = args.open
    copy_to_clip = args.copy

    if not extensions:
        print("Possible extensions: " + " ".join(get_possible_extensions()))
        extensions = input(ENTER_EXTENSIONS_PROMPT).split()

    extensions = filter_allowed_extensions(extensions)

    if not extensions:
        print("No valid extensions provided. Exiting.")
        return

    collected_files = collect_files(extensions)

    if not collected_files:
        print("No files found with the specified extensions.")
        return

    display_files(collected_files)

    do_extract = do_extract or (input("Do you want to extract content? (y/n): ").lower() == "y")

    if do_extract:
        if extract_all:
            selected_indices = range(len(collected_files))
        else:
            selected_indices_input = input(SELECT_INDICES_PROMPT)
            if selected_indices_input.strip() == "":
                selected_indices = range(len(collected_files))
            else:
                selected_indices = [int(i) for i in selected_indices_input.split()]

        output_file = "output.txt"
        with open(output_file, "w") as output:
            for index in selected_indices:
                if 0 <= index < len(collected_files):
                    selected_file = collected_files[index]
                    output.write(f"{selected_file} :\n\n")
                    with open(selected_file, "r") as file_content:
                        output.write(file_content.read())
                    output.write("\n\n—---------------------------------------—\n\n")

        print(f"Content saved in {output_file}")

        if open_file:
            open_file_in_default_app(output_file)

        if copy_to_clip:
            try:
                with open(output_file, "r") as file_content:
                    content = file_content.read()
                    copy_to_clipboard(content)
                    print("Content copied to clipboard.")
            except FileNotFoundError:
                print(f"The file {output_file} was not found. No content was copied.")
            except Exception as e:
                print(f"An error occurred while copying contents to the clipboard: {e}")
    else:
        print("Skipping extraction.")

if __name__ == "__main__":
    main()