#!/usr/bin/env python3

import sys
import os
import io
import json
import zipfile
import time

try:
    import requests
except ImportError:
    requests = None

from rctl.config import load_config

SERVER_URL = ""
AUTH_TOKEN = ""
PROJECT_NAME = ""


def main():
    global SERVER_URL, AUTH_TOKEN, PROJECT_NAME

    config = load_config()
    SERVER_URL = config.get("SERVER_URL", "")
    AUTH_TOKEN = config.get("AUTH_TOKEN", "")
    PROJECT_NAME = config.get("PROJECT_NAME", "rctl_project")

    if not SERVER_URL or SERVER_URL == "https://your-tunnel-url.trycloudflare.com":
        print("Error: PUBLIC_URL is not set in your .env file.")
        print("Please create a .env file containing: PUBLIC_URL=https://your-tunnel-url.trycloudflare.com")
        sys.exit(1)

    if not PROJECT_NAME:
        print("Error: PROJECT_NAME is not set in your .env file.")
        print("Please create a .env file containing: PROJECT_NAME=your_project_name")
        sys.exit(1)

    if requests is None:
        print("Error: The 'requests' package is required but is not installed.")
        sys.exit(1)

    endpoint = f"{SERVER_URL.rstrip('/')}/exec"

    if len(sys.argv) > 1:
        full_command = " ".join(sys.argv[1:])
        if full_command.lower() == "sync":
            sync_repository()
            sys.exit(0)
        task_id = send_command(full_command, endpoint)
        if task_id:
            result = poll_task(task_id, SERVER_URL)
            if result:
                sys.exit(result["exit_code"])
        sys.exit(1)
    else:
        start_interactive_shell()


def send_command(command: str, endpoint: str):
    try:
        headers = {}
        if AUTH_TOKEN:
            headers["X-Auth-Token"] = AUTH_TOKEN
        response = requests.post(endpoint, json={"command": command}, headers=headers, timeout=10)
        if response.status_code == 200:
            res = response.json()
            if "error" in res:
                print(f"Error: {res['error']}")
                return None
            return res.get("task_id")
        print(f"\n[Client Error] Server status: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n[Client Error] Connection failed: {e}")
        return None


def poll_task(task_id: str, server_url: str):
    status_url = f"{server_url.rstrip('/')}/task/{task_id}"
    headers = {}
    if AUTH_TOKEN:
        headers["X-Auth-Token"] = AUTH_TOKEN

    current_cwd = ""
    while True:
        try:
            response = requests.get(status_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"Error: {data['error']}")
                    return None

                if data.get("stdout"):
                    print(data["stdout"], end="", flush=True)
                if data.get("stderr"):
                    print(data["stderr"], file=sys.stderr, end="", flush=True)

                if data.get("completed"):
                    return {
                        "exit_code": data.get("exit_code", 1),
                        "cwd": data.get("cwd", current_cwd)
                    }
            else:
                print(f"\n[Client Error] Polling failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"\n[Client Error] Connection lost: {e}")
            return None
        time.sleep(0.5)


def sync_repository():
    print("Syncing local repository with remote server...")
    zip_buffer = io.BytesIO()
    include_dirs = ["include", "src", "tests", "scripts", "tools"]
    include_files = ["CMakeLists.txt", "CMakePresets.json", "README.md"]

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in include_files:
                if os.path.exists(f):
                    zipf.write(f, f)
            for d in include_dirs:
                if os.path.exists(d):
                    for root, dirs, files in os.walk(d):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, ".")
                            zipf.write(full_path, rel_path)

        zip_buffer.seek(0)
        upload_url = f"{SERVER_URL.rstrip('/')}/upload"
        files = {"file": ("repo.zip", zip_buffer, "application/zip")}
        headers = {}
        if AUTH_TOKEN:
            headers["X-Auth-Token"] = AUTH_TOKEN
        response = requests.post(upload_url, files=files, headers=headers, timeout=20)
        if response.status_code == 200:
            res = response.json()
            if res.get("status") == "success":
                print("Sync successful! Repository updated on server.")
                return True
            else:
                print(f"Sync failed: {res.get('message')}")
        else:
            print(f"Sync failed with server status: {response.status_code}")
    except Exception as e:
        print(f"Connection failed during sync: {e}")
    return False


def start_interactive_shell():
    endpoint = f"{SERVER_URL.rstrip('/')}/exec"
    current_cwd = ""

    print("=== Connected to Remote Interactive Shell ===")
    print("Special Commands:")
    print("  sync   - Sync local repository files to server")
    print("  exit   - Close shell session")
    print("  clear  - Clear terminal screen\n")

    while True:
        try:
            prompt = f"\033[1;32mremote\033[0m:\033[1;34m{current_cwd}\033[0m$ "
            command = input(prompt).strip()

            if not command:
                continue
            if command.lower() in ["exit", "quit"]:
                print("Closing session.")
                break
            if command.lower() == "clear":
                print("\033[H\033[2J", end="")
                continue
            if command.lower() == "sync":
                sync_repository()
                continue

            task_id = send_command(command, endpoint)

            if task_id:
                result = poll_task(task_id, SERVER_URL)
                if result:
                    current_cwd = result.get("cwd", current_cwd)

        except (KeyboardInterrupt, EOFError):
            print("\nClosing session.")
            break


if __name__ == "__main__":
    main()
