import os
import re
import json
import time
import base64
import shutil
import asyncio
import requests
import platform
import subprocess
import threading
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Set environment variables
FILE_PATH = os.environ.get('FILE_PATH', './.cache')
PROJECT_URL = os.environ.get('URL', '') # 填写项目分配的url可实现自动访问，例如：https://www.google.com，留空即不启用该功能
INTERVAL_SECONDS = int(os.environ.get("TIME", 120))                   # 访问间隔时间，默认120s，单位：秒
UUID = os.environ.get('UUID', '01010101-0101-0101-0101-010101010101')
NEZHA_SERVER = os.environ.get('NEZHA_SERVER', 'nz.abcd.com')        # 哪吒3个变量不全不运行
NEZHA_PORT = os.environ.get('NEZHA_PORT', '5555')                  # 哪吒端口为443时开启tls
NEZHA_KEY = os.environ.get('NEZHA_KEY', '')
DOMAIN = os.environ.get('DOMAIN', 'n1.mcst.io')                 # 分配的域名或反代的域名，不带前缀，例如：n1.mcst.io
NAME = os.environ.get('NAME', 'Vls')
PORT = int(os.environ.get('PORT', 3000))            # http服务端口
VPORT = int(os.environ.get('VPORT', 443))          # 节点端口,游戏玩具类需改为分配的端口,并关闭节点的tls

# Create directory if it doesn't exist
if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)
    print(f"{FILE_PATH} has been created")
else:
    print(f"{FILE_PATH} already exists")

# Clean old files
paths_to_delete = ['list.txt','sub.txt', 'swith', 'web']
for file in paths_to_delete:
    file_path = os.path.join(FILE_PATH, file)
    try:
        os.unlink(file_path)
        print(f"{file_path} has been deleted")
    except Exception as e:
        print(f"Skip Delete {file_path}")

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello World')
            
        elif self.path == f'/{SUB_PATH}':
            try:
                with open(sub_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass
    

# Generate xr-ay config file
def generate_config():
    config = {"log": {"access": "/dev/null", "error": "/dev/null", "loglevel": "none",}, "inbounds": [{"port": VPORT, "protocol": "vless", "settings": {"clients": [{"id": UUID, "flow": "xtls-rprx-vision"}], "decryption": "none", "fallbacks": [{"dest": 3001}, {"path": "/vless", "dest": 3002},],}, "streamSettings": {"network": "tcp",},}, {"port": 3001, "listen": "127.0.0.1", "protocol": "vless", "settings": {"clients": [{"id": UUID}], "decryption": "none"}, "streamSettings": {"network": "ws", "security": "none"}}, {"port": 3002, "listen": "127.0.0.1", "protocol": "vless", "settings": {"clients": [{"id": UUID, "level": 0}], "decryption": "none"}, "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": "/vless"}}, "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "metadataOnly": False}},], "dns": {"servers": ["https+local://8.8.8.8/dns-query"]}, "outbounds": [{"protocol": "freedom"}, {"tag": "WARP", "protocol": "wireguard", "settings": {"secretKey": "YFYOAdbw1bKTHlNNi+aEjBM3BO7unuFC5rOkMRAz9XY=", "address": ["172.16.0.2/32", "2606:4700:110:8a36:df92:102a:9602:fa18/128"], "peers": [{"publicKey": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=", "allowedIPs": ["0.0.0.0/0", "::/0"], "endpoint": "162.159.193.10:2408"}], "reserved": [78, 135, 76], "mtu": 1280}},], "routing": {"domainStrategy": "AsIs", "rules": [{"type": "field", "domain": ["domain:openai.com", "domain:ai.com"], "outboundTag": "WARP"},]}}

    with open(os.path.join(FILE_PATH, 'config.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)

generate_config()

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
    files_to_authorize = ['./swith', './web']
    authorize_files(files_to_authorize)

    # Run ne-zha
    NEZHA_TLS = ''
    if NEZHA_SERVER and NEZHA_PORT and NEZHA_KEY:
        NEZHA_TLS = '--tls' if NEZHA_PORT == '443' else ''
        command = f"nohup {FILE_PATH}/swith -s {NEZHA_SERVER}:{NEZHA_PORT} -p {NEZHA_KEY} {NEZHA_TLS} >/dev/null 2>&1 &"
        try:
            subprocess.run(command, shell=True, check=True)
            print('swith is running')
            subprocess.run('sleep 1', shell=True)  # Wait for 1 second
        except subprocess.CalledProcessError as e:
            print(f'swith running error: {e}')
    else:
        print('NEZHA variable is empty, skip running')

    # Run xr-ay
    command1 = f"nohup {FILE_PATH}/web -c {FILE_PATH}/config.json >/dev/null 2>&1 &"
    try:
        subprocess.run(command1, shell=True, check=True)
        print('web is running')
        subprocess.run('sleep 1', shell=True)  # Wait for 1 second
    except subprocess.CalledProcessError as e:
        print(f'web running error: {e}')

    subprocess.run('sleep 3', shell=True)  # Wait for 3 seconds
	

# Return file information based on system architecture
def get_files_for_architecture(architecture):
    if architecture == 'arm':
        return [
            {'file_name': 'swith', 'file_url': 'https://github.com/eooce/test/releases/download/ARM/swith'},
            {'file_name': 'web', 'file_url': 'https://github.com/eooce/test/releases/download/ARM/web'},
        ]
    elif architecture == 'amd':
        return [
            {'file_name': 'swith', 'file_url': 'https://github.com/eooce/test/releases/download/bulid/swith'},
            {'file_name': 'web', 'file_url': 'https://github.com/eooce/test/releases/download/123/web'},
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



# Generate list and sub info
def generate_links():
    print('\033c', end='')
    print('App is running')
    print('Thank you for using this script, enjoy!')
         

# Main function to start the server
async def start_server():
 
    cleanup_old_files()
    create_directory()

    await download_files_and_run()
    
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()   
   
def run_server():
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Server is running on port {PORT}")
    print(f"Running done！")
    print(f"\nLogs will be delete in 90 seconds")
    server.serve_forever()
    
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server()) 
    
    while True:
        time.sleep(3600)
        
if __name__ == "__main__":
    run_async()
