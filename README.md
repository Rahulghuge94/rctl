# rctl

rctl is a lightweight remote-control toolkit designed for secure machine interaction over a tunnel. It lets you send commands to a remote host, work through an interactive shell, and sync project files without exposing your environment to the public internet.

The project is built around a simple idea:
- run a small server on the remote machine,
- expose it through a secure tunnel,
- authenticate every request with a shared token,
- and interact with it from your local machine through a CLI.

## Why rctl?

rctl is useful when you want to:
- remotely execute commands on a machine you control,
- manage deployments or maintenance tasks from your laptop,
- interact with a remote environment securely over a temporary tunnel,
- quickly sync repository content to a server for testing or automation.

## Features

- Secure command execution over authenticated HTTP requests
- Interactive remote shell experience
- Repository sync support for uploading local project files
- Safe archive extraction for uploaded repositories
- Simple configuration through environment variables or a .env file
- Optional Cloudflare tunnel support for public access without exposing raw services

## Architecture

The project has two main parts:
- a client CLI that sends commands and polls for results
- a server component that runs commands, tracks task output, and accepts uploads

Requests are protected with an authentication token, and the server only accepts commands after verifying that token.

## Requirements

- Python 3.9 or newer
- pip
- Optional: Cloudflare tunnel support via cloudflared

## Installation

Clone the repository and install it locally:

```bash
git clone <your-repo-url>
cd rctl
pip install -e .
```

## Configuration

Copy the example environment file and update it:

```bash
copy .example.env .env
```

Then edit .env with your values:

```env
PUBLIC_URL="https://your-tunnel-url.trycloudflare.com"
AUTH_TOKEN="your-secret-token"
PROJECT_NAME="my_project"
```

### Configuration Notes

- PUBLIC_URL is the public address used by the client to reach the server.
- AUTH_TOKEN is required for secure access.
- PROJECT_NAME is used for project-specific upload handling.
- CL_TUNNEL_TOKEN is optional if you want to use a Cloudflare tunnel token instead of a quick tunnel.

## Running the Server

Start the server on the remote machine:

```bash
python -m rctl.rctl_server
```

The server will:
- start the API service,
- generate a token if none is configured,
- and attempt to expose the service through a tunnel if possible.

## Using the Client

Once the server is reachable, you can send commands from your local machine:

```bash
rctl_cli "uname -a"
```

Start an interactive shell:

```bash
rctl_cli
```

Inside the shell, you can use:
- sync - upload the current repository contents to the remote server
- exit - close the shell
- clear - clear the terminal output

## Syncing Files

To sync a project directory to the remote server:

```bash
rctl_cli sync
```

This packages selected project files and uploads them to the remote server for use in the target environment.

## Security Considerations

This tool is designed for controlled, authenticated remote access. A few important safeguards are built in:

- every request must include a shared auth token,
- uploaded archives are validated before extraction,
- path traversal is rejected during repository extraction,
- the server refuses requests without authentication.

For production or shared environments, use a strong token and avoid exposing the service without proper access controls.

## Project Structure

```text
rctl/
  __init__.py
  config.py
  rctl_cli.py
  rctl_server.py
scripts/
  generate_auth_token.py
tests/
  test_config.py
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
