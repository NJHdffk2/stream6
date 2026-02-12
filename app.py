import os
import re
import shutil
import requests
import subprocess
import json
import time

# Set environment variables
FILE_PATH = os.environ.get('FILE_PATH', './.cache')
UUID = os.environ.get('UUID', '01010101-0101-0101-0101-010101010101')  
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')            
ARGO_PORT = int(os.environ.get('ARGO_PORT', '8080'))  

# Create directory if it doesn't exist
if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)
    print(f"{FILE_PATH} has been created")
else:
    print(f"{FILE_PATH} already exists")

# Clean old files
paths_to_delete = ['cat', 'dog', 'mouse.json']
for file in paths_to_delete:
    file_path = os.path.join(FILE_PATH, file)
    try:
        os.unlink(file_path)
        print(f"{file_path} has been deleted")
    except Exception as e:
        print(f"Skip Delete {file_path}")


# Determine system architecture
def get_system_architecture():
    arch = os.uname().machine
    if 'arm' in arch or 'aarch64' in arch or 'arm64' in arch:
        return 'arm'
    else:
        return 'amd'

# Download file
def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    with requests.get(file_url, stream=True) as response, open(file_path, 'wb') as file:
        shutil.copyfileobj(response.raw, file)

# Download and run files
def download_files_and_run():
    architecture = get_system_architecture()
    files_to_download = get_files_for_architecture(architecture)

    if not files_to_download:
        print("Can't find a file for the current architecture")
        return

    for file_info in files_to_download:
        try:
            download_file(file_info['file_name'], file_info['file_url'])
            print(f"Downloaded {file_info['file_name']} successfully")
        except Exception as e:
            print(f"Download {file_info['file_name']} failed: {e}")

    # Authorize and run
    files_to_authorize = ['./cat', './dog']
    authorize_files(files_to_authorize)
    
    # Generate configuration file
    config ={"log":{"access":"/dev/null","error":"/dev/null","loglevel":"none",},"inbounds":[{"port":ARGO_PORT ,"listen":"0.0.0.0","protocol":"vless","settings":{"clients":[{"id":UUID }],"decryption":"none"},"streamSettings":{"network":"ws","wsSettings":{"path":"/"}}}],"outbounds":[{"protocol":"freedom","settings": {}}]}
    with open(os.path.join(FILE_PATH, 'mouse.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)
       
    # Run xr-ay
    command1 = f"nohup {FILE_PATH}/cat -c {FILE_PATH}/mouse.json >/dev/null 2>&1 &"
    try:
        subprocess.run(command1, shell=True, check=True)
        print('cat is running')
        subprocess.run('sleep 1', shell=True)  # Wait for 1 second
    except subprocess.CalledProcessError as e:
        print(f'cat running error: {e}')

    # Run cloud-fared
    if os.path.exists(os.path.join(FILE_PATH, 'dog')):
	# Get command line arguments for cloud-fared
        if not re.match(r'^[A-Z0-9a-z=]{120,250}$', ARGO_AUTH):
            print("ARGO_AUTH variable is empty")
            return
        else:
            args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {ARGO_AUTH}"

        try:
            subprocess.run(f"nohup {FILE_PATH}/dog {args} >/dev/null 2>&1 &", shell=True, check=True)
            print('dog is running')
            subprocess.run('sleep 2', shell=True)  # Wait for 2 seconds
        except subprocess.CalledProcessError as e:
            print(f'Error executing command: {e}')

    subprocess.run('sleep 3', shell=True)  # Wait for 3 seconds


# Return file information based on system architecture
def get_files_for_architecture(architecture):
    if architecture == 'arm':
        return [
            {'file_name': 'cat', 'file_url': 'https://arm64.ssss.nyc.mn/web'},
            {'file_name': 'dog', 'file_url': 'https://arm64.ssss.nyc.mn/2go'},
        ]
    elif architecture == 'amd':
        return [
            {'file_name': 'cat', 'file_url': 'https://arm64.ssss.nyc.mn/web'},
            {'file_name': 'dog', 'file_url': 'https://arm64.ssss.nyc.mn/2go'},
        ]
    return []

# Authorize files
def authorize_files(file_paths):
    new_permissions = 0o775

    for relative_file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, relative_file_path)
        try:
            os.chmod(absolute_file_path, new_permissions)
            print(f"Empowerment success for {absolute_file_path}: {oct(new_permissions)}")
        except Exception as e:
            print(f"Empowerment failed for {absolute_file_path}: {e}")



download_files_and_run()

