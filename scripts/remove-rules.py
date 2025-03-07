#!/usr/bin/env python3
import os
import argparse

def remove_rules_files(apps=None):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    apps_dir = os.path.join(root_dir, 'Apps')
    
    print(f"Root directory: {root_dir}")
    print(f"Looking in Apps directory: {apps_dir}")
    
    if not os.path.exists(apps_dir):
        print(f"Apps directory not found at: {apps_dir}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Directory contents at root: {os.listdir(root_dir)}")
        return
    
    if apps and apps.strip():
        target_apps = [app.strip() for app in apps.split(',')]
        print(f"Processing specific apps: {target_apps}")
    else:
        target_apps = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))]
        print(f"Processing all apps found: {target_apps}")
    
    files_removed = 0
    
    for app in target_apps:
        app_path = os.path.join(apps_dir, app)
        print(f"\nChecking app directory: {app_path}")
        
        if not os.path.exists(app_path):
            print(f"Warning: App directory '{app}' not found")
            continue
            
        try:
            dir_contents = os.listdir(app_path)
            print(f"Contents of {app_path}: {dir_contents}")
        except Exception as e:
            print(f"Error listing contents: {str(e)}")
            
        filenames = ['.rules', '.rules.yaml']
        
        for filename in filenames:
            file_path = os.path.join(app_path, filename)
            print(f"Checking for: {file_path}")
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed: {os.path.relpath(file_path, root_dir)}")
                    files_removed += 1
                except Exception as e:
                    print(f"Error removing {file_path}: {str(e)}")
            else:
                print(f"File not found: {file_path}")
    
    if files_removed == 0:
        print("\nNo rules files were found to remove. Verify that:")
        print("1. Files are named exactly '.rules' or '.rules.yaml' (no additional extensions)")
        print("2. Files exist in the Apps/[appname] directories")
        print("3. The app names provided (if any) match directory names")
        print(f"4. Current working directory is correct (root: {root_dir})")
    else:
        print(f"\nTotal files removed: {files_removed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove .rules and .rules.yaml files from Apps directories"
    )
    parser.add_argument(
        "--apps",
        type=str,
        default=None,
        help="Comma-separated list of app names to process (leave empty for all)"
    )
    
    args = parser.parse_args()
    remove_rules_files(args.apps)