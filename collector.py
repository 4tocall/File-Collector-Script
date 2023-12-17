import os
import argparse
import subprocess
import platform

IGNORED_DIRECTORIES = {'__pycache__', '.git', '.idea', '.vscode', '__init__', 'build', 'dist', 'venv', 'node_modules', 'env', '.venv', '.mypy_cache', '.pytest_cache', '.vs', '__pycache__', '.ipynb_checkpoints', '.mypy_cache', '.pylint', '.pytest_cache', '.tox', '.serverless', '.local', '.history', '.eggs', '*.egg-info', '*.DS_Store'}

ALLOWED_EXTENSIONS = {'js', 'jsx', 'html', 'json', 'xml', 'yaml', 'yml', 'scss', 'sass', 'css', 'py', 'php', 'md', 'java', 'cpp', 'h', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'tar', 'gz', 'sql', 'cs', 'swift', 'go', 'ts', 'tsx', 'rs', 'kt', 'sh', 'vue', 'scala'}

ENTER_EXTENSIONS_PROMPT = "Enter file extensions separated by spaces: "
SELECT_INDICES_PROMPT = "Enter the indices of the files you want to collect (separated by spaces), or press Enter for 'all': "
ENTER_FILE_NAME_PROMPT = "Enter the output file name (default is 'output.txt'): "
SELECT_METHOD_PROMPT = "Select method: Copy to clipboard or Output to file: "
OPEN_FILE_PROMPT = "Open the generated file in the default app? (y/n): "
COPY_CONTENT_PROMPT = "Copy the content to the clipboard? (y/n): "
CONTENT_SAVED_MESSAGE = "Content saved in {}"
COPY_SUCCESS_MESSAGE = "Content copied to clipboard."
NO_EXTENSION_MESSAGE = "No valid extensions provided. Exiting."
NO_FILES_FOUND_MESSAGE = "No files found with the specified extensions."
FILE_NOT_FOUND_MESSAGE = "The file {} was not found. No content was copied."
ERROR_COPY_MESSAGE = "An error occurred while copying contents to the clipboard: {}"

def color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

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
    
    if system_platform == "Darwin":
        subprocess.run(["pbcopy"], input=content.encode("utf-8"))
    elif system_platform == "Linux":
        try:
            subprocess.run(["xclip", "-selection", "clipboard"], input=content.encode("utf-8"))
        except FileNotFoundError:
            print(color("Command 'xclip' not found. Please install xclip or use a package like pyperclip.", "1;31;40"))
    elif system_platform == "Windows":
        subprocess.run(["clip"], input=content.encode("utf-8"), shell=True)
    else:
        print(color("Clipboard copy not supported on this platform. Please use a package like pyperclip.", "1;31;40"))

def open_file_in_default_app(file_path):
    system_platform = platform.system()

    if system_platform == "Darwin":
        subprocess.run(["open", file_path])
    elif system_platform == "Linux":
        subprocess.run(["xdg-open", file_path])
    elif system_platform == "Windows":
        subprocess.run(["start", "notepad", file_path], shell=True)
    else:
        print(color("Opening files not supported on this platform.", "1;31;40"))

def stylized_prompt(prompt_message):
    return input(color(prompt_message, "1;37;40"))

def get_valid_indices(selected_indices_input, total_files):
    try:
        selected_indices = [int(i) for i in selected_indices_input.split()]
        if all(0 <= index < total_files for index in selected_indices):
            return selected_indices
    except ValueError:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='File Collector')
    parser.add_argument('extensions', nargs='*', default=[], choices=list(ALLOWED_EXTENSIONS), help='File extensions to collect')
    parser.add_argument('-extract', action='store_true', help='Extract content')
    parser.add_argument('-all', action='store_true', help='Extract all files')
    parser.add_argument('-open', action='store_true', help='Open the generated file in the default app')
    parser.add_argument('-copy', action='store_true', help='Copy the content to the clipboard')
    parser.add_argument('--output', help='Specify the output file name')

    args = parser.parse_args()

    extensions = args.extensions
    do_extract = args.extract
    extract_all = args.all
    open_file = args.open
    copy_to_clip = args.copy
    output_file_name = args.output

    if not extensions:
        print(color("Possible extensions: " + " ".join(get_possible_extensions()), "1;31;40"))
        extensions = stylized_prompt(ENTER_EXTENSIONS_PROMPT).split()

    extensions = filter_allowed_extensions(extensions)

    if not extensions:
        print(color(NO_EXTENSION_MESSAGE, "1;31;40"))
        return

    collected_files = collect_files(extensions)

    if not collected_files:
        print(color(NO_FILES_FOUND_MESSAGE, "1;31;40"))
        return

    display_files(collected_files)

    do_extract = do_extract or (copy_to_clip or extract_all or open_file or (len(collected_files) == 1 and stylized_prompt("Do you want to extract content? (y/n): ").lower() == "y"))

    if do_extract:
        if extract_all:
            selected_indices = range(len(collected_files))
        elif len(collected_files) == 1:
            selected_indices = [0]
        else:
            while True:
                selected_indices_input = stylized_prompt(SELECT_INDICES_PROMPT)
                if selected_indices_input.strip() == "":
                    selected_indices = range(len(collected_files))
                    break
                valid_indices = get_valid_indices(selected_indices_input, len(collected_files))
                if valid_indices is not None:
                    selected_indices = valid_indices
                    break
                else:
                    print(color("Invalid indices. Please enter valid indices.", "1;31;40"))

        if not output_file_name:
            output_file_name = stylized_prompt(ENTER_FILE_NAME_PROMPT) if not copy_to_clip else "output.txt"

        if not output_file_name.endswith('.txt'):
            output_file_name += '.txt'

        if copy_to_clip:
            content = ""
            for index in selected_indices:
                if 0 <= index < len(collected_files):
                    selected_file = collected_files[index]
                    with open(selected_file, "r") as file_content:
                        content += f"// {selected_file} :\n\n"
                        content += file_content.read()
                        content += "\n\n"
            copy_to_clipboard(content)
            print(color(COPY_SUCCESS_MESSAGE, "1;32;40"))
        else:
            with open(output_file_name, "w") as output:
                for index in selected_indices:
                    if 0 <= index < len(collected_files):
                        selected_file = collected_files[index]
                        output.write(f"// {selected_file} :\n\n")
                        with open(selected_file, "r") as file_content:
                            output.write(file_content.read())
                        output.write("\n\n")

            print(color(CONTENT_SAVED_MESSAGE.format(output_file_name), "1;32;40"))

            if open_file:
                open_file_in_default_app(output_file_name)

if __name__ == "__main__":
    main()
