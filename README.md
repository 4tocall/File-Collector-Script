
### File Collector Script

  

#### Description:

  

The File Collector script is a command-line utility designed to collect and extract content from specified files within a directory tree. It supports various file types and provides options for extracting content, opening the generated file in the default app, and copying content to the clipboard.

  

#### Installation:

  

1.  **Clone the Repository:**

  

```bash

git clone <repository-url>

cd <repository-directory>

```

3.  **Install Dependencies (Optional):**

The script uses standard Python libraries. Ensure you have Python installed on your system.

4.  **Set Up Aliases:**

-  **Zsh:**

- Open your Zsh configuration file, usually `~/.zshrc`, in a text editor.

```bash

nano ~/.zshrc

```

- Add the following line to create an alias that allows passing arguments:

```bash

alias collect='python /path/to/file_collector_script.py $@'

```

- Save and exit the editor.

- Reload your Zsh configuration:

```bash

source ~/.zshrc

```

-  **Bash:**

- Open your Bash configuration file, usually `~/.bashrc`, in a text editor.

```bash

nano ~/.bashrc

```

- Add the following line to create an alias that allows passing arguments:

```bash

alias collect='python /path/to/file_collector_script.py $@'

```

- Save and exit the editor.

- Reload your Bash configuration:

```bash

source ~/.bashrc

```

  

#### Usage:

  

- Run the script using the alias you've set up:

```bash

collect [options]

```

- Options:

-  `-extract`: Extract content from selected files.

-  `-all`: Extract content from all collected files.

-  `-open`: Open the generated file in the default app.

-  `-copy`: Copy the content to the clipboard.

-  `extensions`: Specify file extensions to collect.

- Example: Collect files with specified extensions, extract content, and open the generated file

  

```bash

collect -extract -open -copy py txt

```

- To view the available options and usage information:

```bash

collect --help

```
