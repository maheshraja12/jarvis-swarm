import os
import fnmatch
import sys

def search_files(filename: str, directory: str = None) -> str:
    """Searches for files matching a keyword/glob pattern in a directory (defaults to User's home folder)."""
    if not directory:
        # Default to user's home directory (Documents is a good sub-target, but home covers Desktop/Downloads too)
        directory = os.path.expanduser("~")
        
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        return f"Directory '{directory}' does not exist, sir."
        
    filename_query = filename.lower().strip()
    matches = []
    
    # Exclude system and giant directories to ensure fast results and prevent hangs
    exclude_dirs = {
        "appdata", "application data", "cookies", "local settings", 
        "sendto", "start menu", "my documents", "templates",
        "node_modules", ".git", "__pycache__", "venv", ".venv",
        "system32", "windows", "program files", "program files (x86)"
    }
    
    max_matches = 15
    max_depth = 3  # Restrict traversal depth for performance
    
    start_depth = directory.rstrip(os.sep).count(os.sep)
    
    try:
        for root, dirs, files in os.walk(directory, topdown=True):
            # Check depth
            depth = root.rstrip(os.sep).count(os.sep) - start_depth
            if depth >= max_depth:
                # Clear dirs to prevent going deeper
                dirs.clear()
                continue
                
            # Filter directories in-place to exclude unwanted ones
            dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                # Match query as substring or glob pattern
                if filename_query in file.lower() or fnmatch.fnmatch(file.lower(), filename_query):
                    full_path = os.path.join(root, file).replace("\\", "/")
                    matches.append(full_path)
                    if len(matches) >= max_matches:
                        break
            
            if len(matches) >= max_matches:
                break
                
        if not matches:
            return f"I searched up to {max_depth} folders deep in '{directory}' but found no files matching '{filename}', sir."
            
        result = f"I found the following files matching '{filename}':\n"
        for path in matches:
            result += f"- {path}\n"
            
        if len(matches) == max_matches:
            result += "(Note: Results capped at 15 items, sir.)"
            
        return result
    except Exception as e:
        return f"An error occurred while searching: {e}"

# Simple self-test if run directly
if __name__ == "__main__":
    print("Searching for project files...")
    print(search_files("requirements", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
