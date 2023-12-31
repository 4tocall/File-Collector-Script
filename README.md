
# File Collector Script

  

## Description:

  

The File Collector script is a command-line utility designed to collect and extract content from specified files within a directory tree. It supports various file types and provides options for extracting content, opening the generated file in the default app, and copying content to the clipboard.

  

## Installation:

    
  
  1.  **Clone the Repository :**
  
    
      
      ```bash
      
      git clone https://github.com/4tocall/File-Collector-Script
      
      ```
  
  3.  **Install Dependencies :**
  
      The script uses standard Python libraries. Ensure you have Python installed on your system.
  
  4.  **Set Up Aliases :**
  
      **Zsh :**
      
      - Open your Zsh configuration file, usually `~/.zshrc`, in a text editor.
      
      ```bash
      
      nano ~/.zshrc
      
      ```
      
      - Add the following line to create an alias that allows passing arguments:
      
      ```bash
      
      alias collect='python /path/to/file_collector_script.py $@'
      
      ```
      
      - Save and exit the editor.
      
      - Reload your Zsh configuration :
      
      ```bash
      
      source ~/.zshrc
      
      ```
      
      **Bash :**
      
      - Open your Bash configuration file, usually `~/.bashrc`, in a text editor.
      
      ```bash
      
      nano ~/.bashrc
      
      ```
      
      - Add the following line to create an alias that allows passing arguments :
      
      ```bash
      
      alias collect='python /path/to/collector.py $@'
      
      ```
      
      - Save and exit the editor.
      
      - Reload your Bash configuration:
      
      ```bash
      
      source ~/.bashrc
      
      ```
  
      Note: Before configuring aliases, ensure you move `collector.py` to a directory of your choice. This allows you to run the script from any location, enhancing flexibility and convenience.
    

## Usage :

  
  
- Run the script using the alias you've set up :
  
    ```bash
    
    collect [options]
    
    ```
  
- Options :

  `extensions`: Specify file extensions to collect.

  `-extract`: Extract content from selected files.
    
  `-all`: Extract content from all collected files.
    
  `-open`: Open the generated file in the default app.
    
  `-copy`: Copy the content to the clipboard.

  `--output` : Specify the output file name when extracting content (e.g., `--output fichier.txt`).
    
  
- Example :

  Collect files with specified extensions, extract content, and open the generated file
  
  
  ```bash
  
  collect py html -extract -open -copy
  
  ```
  
  To view the available options and usage information :
    
    ```bash
  
    collect --help
    
    ```
