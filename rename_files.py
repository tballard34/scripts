import os
import re

def standardize_name(name):
    """
    Standardize the name according to the rules:
    - Replace '&' with 'and'
    - Convert camelCase to snake_case
    - Convert to lowercase
    - Replace spaces, dashes, and other separators with underscores
    - Remove special characters except alphanumeric, underscores, and dots
    """
    # List of files/patterns to preserve exactly as-is
    preserved_names = {
        # System files
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        # Git files
        '.git', '.gitignore', '.gitattributes', 'README.md', 'LICENSE',
        # Node/JS files
        'package.json', 'package-lock.json', 'node_modules',
        # Python files
        '__init__.py', '__pycache__', 'requirements.txt', 'setup.py', 'setup.cfg',
        # Config files
        '.env', '.editorconfig', '.eslintrc', '.prettierrc', '.babelrc',
        # Build files
        'Makefile', 'CMakeLists.txt', 'Dockerfile', 'docker-compose.yml',
        # IDE files
        '.vscode', '.idea', '.project', '.classpath',
        # Common web files
        'favicon.ico', 'robots.txt', 'sitemap.xml',
        # Documentation
        'CHANGELOG.md', 'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md',
        # Temp files
        '~$*',  # Microsoft Office temp files
        '.#*',  # Emacs temp files
        '*.swp', # Vim temp files
        # Config files
        '.htaccess', 'web.config', 'app.config',
        # Build outputs
        'dist', 'build', 'target', 'out',
        # Database files
        '.sqlite', '.db',
        # Log files
        '*.log', 'logs',
        # Cache directories
        '.cache', '.tmp', 'temp',
        # Package manager files
        'yarn.lock', 'composer.json', 'composer.lock',
        # CI/CD files
        '.travis.yml', '.gitlab-ci.yml', 'jenkins.yml',
        # Test files
        'phpunit.xml', 'jest.config.js', 'karma.conf.js',
        # Security files
        '.npmrc', '.yarnrc', '.dockerignore',
        # Framework specific
        'angular.json', 'tsconfig.json', 'webpack.config.js',
        # OS specific
        '.bashrc', '.bash_profile', '.zshrc',
        # Backup files
        '*.bak', '*.backup', '*.old',
        # Certificate files
        '*.pem', '*.crt', '*.key',
        # Font files
        '*.ttf', '*.otf', '*.woff', '*.woff2',
        # Media placeholder files
        '.keep', '.gitkeep',
        # Common config files
        'config.yml', 'config.json', 'settings.json',
        # Dependency files
        'Gemfile', 'Gemfile.lock', 'requirements.in',
        # Shell scripts
        '*.sh', '*.bash', '*.zsh',
        # Version files
        'VERSION', '.ruby-version', '.python-version',
        # Project files
        '.project', '.buildpath', '.settings',
        # Resource files
        '*.rc', '.mailmap', '.gvimrc',
        # Meta files
        'META-INF', 'MANIFEST.MF',
        # Template files
        '*.template', '*.tpl',
        # System files
        'lost+found',
        # Misc development files
        '.flowconfig', '.watchmanconfig', '.buckconfig',
        # Documentation generators
        'mkdocs.yml', 'sphinx.conf', 'doxygen.conf'
    }
    
    # Check if the name should be preserved
    if name in preserved_names or any(name.endswith(pat.replace('*', '')) for pat in preserved_names if '*' in pat):
        return name
        
    # Original standardization logic continues here...
    name = name.replace('&', 'and')
    name = re.sub(r'(?<!^)(?<![\W_])([A-Z])', r'_\1', name)
    name = name.lower()
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'[^a-z0-9_.]', '', name)
    return name

def get_unique_path(path):
    """
    Generate a unique path by adding a number suffix if the path already exists.
    """
    if not os.path.exists(path):
        return path
    
    # Split the path into base and extension
    base, ext = os.path.splitext(path)
    counter = 1
    
    # Keep trying new numbers until we find an unused path
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    
    return f"{base}_{counter}{ext}"

def rename_files_recursive(directory):
    """
    Recursively rename files in the directory and subdirectories.
    """
    # First collect all paths to avoid modification during iteration
    all_files = []
    all_dirs = []
    
    for root, dirs, files in os.walk(directory, topdown=False):
        # Collect file paths
        for file in files:
            all_files.append((root, file))
        # Collect directory paths
        for dir_name in dirs:
            all_dirs.append((root, dir_name))
    
    # Process all files first
    for root, file in all_files:
        # Generate the new file name
        new_name = standardize_name(file)
        # Construct full file paths
        old_path = os.path.join(root, file)
        new_path = os.path.join(root, new_name)
        
        # Get a unique path if there would be a naming conflict
        if old_path.lower() != new_path.lower():  # Case-insensitive comparison
            new_path = get_unique_path(new_path)
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")
    
    # Process directories from deepest to shallowest
    for root, dir_name in reversed(all_dirs):
        # Standardize the directory name
        new_dir_name = standardize_name(dir_name)
        old_dir_path = os.path.join(root, dir_name)
        new_dir_path = os.path.join(root, new_dir_name)
        
        # Get a unique path if there would be a naming conflict
        if old_dir_path.lower() != new_dir_path.lower():  # Case-insensitive comparison
            new_dir_path = get_unique_path(new_dir_path)
            os.rename(old_dir_path, new_dir_path)
            print(f"Renamed Directory: {old_dir_path} -> {new_dir_path}")

# Specify the root directory to start renaming
if __name__ == "__main__":
    root_directory = input("Enter the root directory path: ").strip()
    if os.path.isdir(root_directory):
        rename_files_recursive(root_directory)
    else:
        print("Invalid directory path.")