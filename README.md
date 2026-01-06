# aridhia-sync

A command line tool to synchronise files from a local directory to an Aridhia Data Platform project.

Based on https://github.com/joshuaspear/aridhia-git-tag-upload by @joshuaspear.

## Installation

1. Clone this repository.
1. Download [`azcopy`](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10) to this directory (or to another directory in your PATH).

Other than `azcopy`, this tool only requires Python standard libraries and does not need any additional packages.

## Usage

### Adding, removing, or listing remotes
- `python main.py add`: Interactively add a new upload destination. You will specify the name of the destination (something memorable) and the URL, which includes a SAS token.
- `python main.py remove <name>`: Removes the remote with the specified name.
- `python main.py clear`: Clears all saved remotes following a confirmation prompt.
- `python main.py list`: Lists all saved remotes.

### Uploading files
`python main.py upload <destination_name> <file_path>`: Uploads the specified file to the specified destination.

If the file path is a directory, all files within that directory (and its subdirectories) will be uploaded, preserving the directory structure. Use `--dry-run` to see which files would be uploaded without actually uploading them.

The following are exluded from upload:
- Files matching the patterns: `*.exe`, `.gitignore`, `*.pyc`
- Directories: `.git`, `__pycache__`, `.venv`
- Distribution directories matching the regex: `.*\.egg-info.*`

