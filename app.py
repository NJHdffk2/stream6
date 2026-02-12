import os
import re
import json
import time
import shutil
import asyncio
import requests
import platform
import subprocess


# Environment variables
FILE_PATH = os.environ.get('FILE_PATH', './.cache')
UUID = os.environ.get('UUID', '01010101-0101-0101-0101-010101010101')  
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')            
ARGO_PORT = int(os.environ.get('ARGO_PORT', '8080'))   


# Create running folder
def create_directory():
    print('\033c', end='')
    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)
        print(f"{FILE_PATH} is created")
    else:
        print(f"{FILE_PATH} already exists")


# Clean up old files
def cleanup_old_files():
    paths_to_delete = ['cat', 'dog', 'boot.log', 'mouse.json']
    for file in paths_to_delete:
        file_path = os.path.join(FILE_PATH, file)
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
            


# Determine system architecture
def get_system_architecture():
    architecture = platform.machine().lower()
    if 'arm' in architecture or 'aarch64' in architecture:
        return 'arm'
    else:
        return 'amd'


# Download file based on architecture
def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Download {file_name} successfully")
        return True
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"Download {file_name} failed: {e}")
        return False


# Get files for architecture
def get_files_for_architecture(architecture):
    if architecture == 'arm':
        base_files = [
            {"fileName": "cat", "fileUrl": "https://arm64.ssss.nyc.mn/web"},
            {"fileName": "dog", "fileUrl": "https://arm64.ssss.nyc.mn/2go"}
        ]
    else:
        base_files = [
            {"fileName": "cat", "fileUrl": "https://amd64.ssss.nyc.mn/web"},
            {"fileName": "dog", "fileUrl": "https://amd64.ssss.nyc.mn/2go"}
        ]

    return base_files
  
# Authorize files with execute permission
def authorize_files(file_paths):
    for relative_file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, relative_file_path)
        if os.path.exists(absolute_file_path):
            try:
                os.chmod(absolute_file_path, 0o775)
                print(f"Empowerment success for {absolute_file_path}: 775")
            except Exception as e:
                print(f"Empowerment failed for {absolute_file_path}: {e}")


# Execute shell command and return output
def exec_cmd(command):
    try:
        process = subprocess.Popen(
            command, 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout + stderr
    except Exception as e:
        print(f"Error executing command: {e}")
        return str(e)

# Download and run necessary files
async def download_files_and_run():
    global private_key, public_key
    
    architecture = get_system_architecture()
    files_to_download = get_files_for_architecture(architecture)
    
    if not files_to_download:
        print("Can't find a file for the current architecture")
        return
    
    # Download all files
    download_success = True
    for file_info in files_to_download:
        if not download_file(file_info["fileName"], file_info["fileUrl"]):
            download_success = False
    
    if not download_success:
        print("Error downloading files")
        return
    
    # Authorize files
    files_to_authorize = ['cat', 'dog'] 
    authorize_files(files_to_authorize)
    
    # Generate configuration file
    config ={"log":{"access":"/dev/null","error":"/dev/null","loglevel":"none",},"inbounds":[{"port":ARGO_PORT ,"listen":"0.0.0.0","protocol":"vless","settings":{"clients":[{"id":UUID }],"decryption":"none"},"streamSettings":{"network":"ws","wsSettings":{"path":"/"}}}],"outbounds":[{"protocol":"freedom","settings": {}}]}
    with open(os.path.join(FILE_PATH, 'mouse.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)
    
       
    # Run 
    command = f"nohup {os.path.join(FILE_PATH, 'cat')} -c {os.path.join(FILE_PATH, 'mouse.json')} >/dev/null 2>&1 &"
    try:
        exec_cmd(command)
        print('cat is running')
        time.sleep(1)
    except Exception as e:
        print(f"cat running error: {e}")
    
    # Run cloud
    if os.path.exists(os.path.join(FILE_PATH, 'dog')):
        if not re.match(r'^[A-Z0-9a-z=]{120,250}$', ARGO_AUTH):
            print("ARGO_AUTH variable is empty")
            return
        else:
            args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {ARGO_AUTH}"
        
        try:
            exec_cmd(f"nohup {os.path.join(FILE_PATH, 'dog')} {args} >/dev/null 2>&1 &")
            print('dog is running')
            time.sleep(2)
        except Exception as e:
            print(f"Error executing command: {e}")
    
    time.sleep(5)
    
   
# Main function to start the server
async def start_server():
    cleanup_old_files()
    create_directory()
    await download_files_and_run()
  
    
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server()) 
    
    while True:
        time.sleep(3600)
        
if __name__ == "__main__":
    run_async()

