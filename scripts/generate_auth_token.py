# generate auth token for the user to access the rctl server
import os
import secrets

def generate_auth_token():
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    token = generate_auth_token()
    print(f"Generated Auth Token: {token}")