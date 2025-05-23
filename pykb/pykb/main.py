import argparse
import os
import glob # Still useful for the glob_pattern itself, though os.walk is primary for traversal
import fnmatch # For matching filenames against the glob_pattern
from pykb.parser import parse_code
from pykb.writer import write_knowledge_base

DEFAULT_EXCLUDE_DIRS = "venv,.env,.git,__pycache__,build,dist,docs,examples,tests,node_modules,*.egg-info"

def main():
    parser = argparse.ArgumentParser(description="PyKB: Python Knowledge Base Generator")
    parser.add_argument(
        "project_path",
        help="Path to the Python project directory to analyze."
    )
    parser.add_argument(
        "-o", "--output",
        default="knowledge_base.json",
        help="Path to save the JSON knowledge base. Default: knowledge_base.json in the current directory."
    )
    parser.add_argument(
        "-g", "--glob",
        default="*.py",
        help="Glob pattern for file matching. Default: *.py"
    )
    parser.add_argument(
        "-e", "--exclude",
        default=DEFAULT_EXCLUDE_DIRS,
        help=f"Comma-separated string of directory or file patterns to exclude. Default: {DEFAULT_EXCLUDE_DIRS}"
    )

    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)
    output_file_path = os.path.abspath(args.output) # Ensure output path is absolute

    if not os.path.isdir(project_path):
        print(f"Error: Project path '{project_path}' does not exist or is not a directory.")
        return

    exclude_patterns = {pattern.strip() for pattern in args.exclude.split(',')}
    
    all_knowledge_units = []
    discovered_files_count = 0
    processed_files_count = 0

    print(f"Starting analysis of project: {project_path}")
    print(f"Output will be saved to: {output_file_path}")
    print(f"File pattern: {args.glob}")
    print(f"Exclude patterns: {exclude_patterns}")

    for root, dirs, files in os.walk(project_path, topdown=True):
        # Prune excluded directories
        # Modify dirs in-place to prevent os.walk from traversing them
        original_dirs = list(dirs) # Iterate over a copy for modification
        for d_name in original_dirs:
            # Check full path and just dir name for exclusion
            if d_name in exclude_patterns or \
               any(fnmatch.fnmatch(d_name, pat) for pat in exclude_patterns if '*' in pat) or \
               os.path.join(os.path.relpath(root, project_path), d_name) in exclude_patterns:
                 if d_name in dirs: # Check if not already removed
                    dirs.remove(d_name)


        for filename in files:
            discovered_files_count +=1
            file_path = os.path.join(root, filename)
            relative_file_path = os.path.relpath(file_path, project_path)

            # Check if the file itself matches any exclude pattern (e.g., *.txt, specific_file.py)
            # Also check if any part of the path matches an exclude pattern (e.g. excluding "tests/data")
            is_excluded_file = False
            path_parts = relative_file_path.split(os.sep)
            
            current_path_check = ""
            for part in path_parts:
                current_path_check = os.path.join(current_path_check, part) if current_path_check else part
                if current_path_check in exclude_patterns:
                    is_excluded_file = True
                    break
            if is_excluded_file:
                continue

            if any(fnmatch.fnmatch(filename, pat) for pat in exclude_patterns if '*' in pat and pat != args.glob):
                continue
            if filename in exclude_patterns: # Exact filename match
                continue


            if fnmatch.fnmatch(filename, args.glob):
                print(f"Processing: {relative_file_path}")
                processed_files_count += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    knowledge_units = parse_code(content)
                    for unit in knowledge_units:
                        unit['filepath'] = relative_file_path.replace(os.sep, '/') # Ensure consistent path separators
                    all_knowledge_units.extend(knowledge_units)
                except Exception as e:
                    print(f"Error processing file {relative_file_path}: {e}")
    
    print(f"\nDiscovered {discovered_files_count} files. Processed {processed_files_count} files matching '{args.glob}'.")

    if not all_knowledge_units and processed_files_count == 0:
        print("No Python files found or processed. Nothing to write to knowledge base.")
    else:
        write_knowledge_base(all_knowledge_units, output_file_path)

if __name__ == '__main__':
    main()
