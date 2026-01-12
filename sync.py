#! /usr/bin/env python3
"""Utility to upload files / folders to Aridhia Data Platform using AzCopy and stored tokens, 
as well as token management."""
import argparse
import dataclasses
import json
from subprocess import call
import os

DESTINATIONS_FILE = "destinations.json" # Local file to store destinations including secret tokens


@dataclasses.dataclass
class Destination:
    """Simple representation of an Aridhia upload destination.
    URL includes the SAS token.
    """
    name: str
    url: str

    def to_json(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return dataclasses.asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "Destination":
        """Deserialize from JSON-compatible dict."""
        return cls(**data)

# pylint: disable=too-many-arguments,too-many-positional-arguments
def upload(
    source: str,
    destination_url: str,
    exclude_patterns: tuple[str, ...] = (),
    exclude_paths: tuple[str, ...] = (),
    exclude_regexps: tuple[str, ...] = (),
    dry_run: bool = False
) -> bool:
    """Upload files from source to destination using AzCopy."""
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source path '{source}' does not exist.")
    call_list = ["azcopy", "copy", source, destination_url]
    if os.path.isdir(source):
        call_list.append("--recursive=true")
        print(f"Uploading directory '{source}' to '{destination_url}'...")
    else:
        print(f"Uploading file '{source}' to '{destination_url}'...")

    if exclude_patterns:
        call_list.append(f"--exclude-pattern={';'.join(exclude_patterns)}")
    if exclude_paths:
        call_list.append(f"--exclude-path={';'.join(exclude_paths)}")
    if exclude_regexps:
        call_list.append(f"--exclude-regex={';'.join(exclude_regexps)}")
    if dry_run:
        call_list.append("--dry-run")
        print("Performing dry run (no files will be uploaded).")

    call(call_list)
    return True

def read_destinations_file() -> list[Destination]:
    """Read the destinations file and return a list of Destination objects."""
    if os.path.exists(DESTINATIONS_FILE):
        with open(DESTINATIONS_FILE, "r", encoding='utf-8') as f:
            return [Destination.from_json(d) for d in json.load(f)]
    return []

def add_destination():
    """Interactively add a new destination."""
    name = input("Enter a name for this upload destination: ")
    url = input("Enter the token URL: ")

    existing_destinations: list[Destination] = read_destinations_file()

    matching_token = next((dest for dest in existing_destinations if dest.url == url), None)
    if matching_token:
        print(f"A destination with this token already exists: {matching_token.name}")
        return

    matching_token = next((dest for dest in existing_destinations if dest.name == name), None)
    if matching_token:
        print(f"A destination with the name '{name}' already exists.")
        return

    new_destination = Destination(name=name, url=url)
    existing_destinations.append(new_destination)
    with open("destinations.json", "w", encoding='utf-8') as f:
        json.dump(existing_destinations, f, indent=4, default=lambda o: o.to_json())
    print(f"Destination '{name}' added successfully.")

def remove_destination(destination_name: str):
    """Remove a destination by name."""
    destinations = read_destinations_file()
    if not destinations:
        print("No destinations found.")
        return
    updated_destinations = [dest for dest in destinations if dest.name != destination_name]
    if len(updated_destinations) == len(destinations):
        print(f"No destination found with the name '{destination_name}'.")
        return
    with open(DESTINATIONS_FILE, "w", encoding='utf-8') as f:
        json.dump(updated_destinations, f, indent=4, default=lambda o: o.to_json())
    print(f"Destination '{destination_name}' removed successfully.")

def clear_destinations():
    """Clear all stored destinations."""
    if os.path.exists(DESTINATIONS_FILE):
        response = input("Are you sure you want to clear all destinations? (y/N): ")
        if response.lower() == "y":
            os.remove(DESTINATIONS_FILE)
            print("All destinations cleared.")
        else:
            print("Clear operation cancelled.")
    else:
        print("No destinations to clear.")

def list_destinations():
    """List all stored destinations."""
    existing_destinations = read_destinations_file()
    if not existing_destinations:
        print("No destinations found.")
        return
    print("Existing destinations:")
    for dest in existing_destinations:
        print(f"- {dest.name}: {dest.url}")

def update_destination(destination_name: str):
    """Update the URL of an existing destination."""
    destinations = read_destinations_file()
    matching_destination = next(
        (dest for dest in destinations if dest.name == destination_name),
        None
    )
    if not matching_destination:
        print(f"No destination found with the name '{destination_name}'.")
        return
    new_url = input(f"Enter the new token URL for destination '{destination_name}': ")
    matching_destination.url = new_url
    with open(DESTINATIONS_FILE, "w", encoding='utf-8') as f:
        json.dump(destinations, f, indent=4, default=lambda o: o.to_json())
    print(f"Destination '{destination_name}' updated successfully.")

def upload_files(source: str, destination_name: str, dry_run: bool = False):
    """Upload files from source to the specified destination.
    
    Simple wrapper around the upload function that looks up the destination by name.
    """
    destinations = read_destinations_file()
    matching_destination = next(
        (dest for dest in destinations if dest.name == destination_name),
    None)
    if not matching_destination:
        print(f"No destination found with the name '{destination_name}'.")
        return
    upload(
        source, 
        matching_destination.url,  
        exclude_patterns=('*.exe', '.gitignore', '*.pyc'), 
        exclude_paths=('.git', '__pycache__', '.venv', '.pytest_cache', '.ruff_cache', '.vscode'),
        exclude_regexps=(r'.*\.egg-info.*',), 
        dry_run=dry_run
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronise files from a local directory to an Aridhia Data Platform project."
    )
    subparsers = parser.add_subparsers(dest="command")

    parser_add = subparsers.add_parser("add", help="Add a new Aridhia destination.")
    parser_remove = subparsers.add_parser("remove", help="Remove an Aridhia destination.")
    parser_remove.add_argument("name", help="Name of the destination to remove.")
    parser_update = subparsers.add_parser("update", help="Update an existing Aridhia destination.")
    parser_update.add_argument("name", help="Name of the destination to update.")
    parser_clear = subparsers.add_parser("clear", help="Clear all Aridhia destinations.")
    parser_list = subparsers.add_parser("list", help="List all Aridhia destinations.")
    parser_upload = subparsers.add_parser("upload", help="Upload files to an Aridhia destination.")
    parser_upload.add_argument("destination",  help="Name of the destination to upload files to.")
    parser_upload.add_argument("source",  help="Source file or directory to upload files from.")
    parser_upload.add_argument("--dry-run", action="store_true",
                               help="Perform a dry run without actual upload.")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()

    if args.command == "add":
        add_destination()
    elif args.command == "remove":
        remove_destination(args.name)
    elif args.command == "clear":
        clear_destinations()
    elif args.command == "list":
        list_destinations()
    elif args.command == "upload":
        upload_files(args.source, args.destination, dry_run=args.dry_run)
    elif args.command == "update":
        update_destination(args.name)
