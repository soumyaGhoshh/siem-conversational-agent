import secrets
import os
import sys

def generate_secret():
    return secrets.token_hex(32)

def update_env(secret):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        return False
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    updated = False
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('JWT_SECRET='):
                f.write(f'JWT_SECRET={secret}\n')
                updated = True
            elif line.startswith('ADMIN_TOKEN='):
                # Remove ADMIN_TOKEN as it's insecure and no longer needed for API
                continue
            else:
                f.write(line)
        
        if not updated:
            f.write(f'\nJWT_SECRET={secret}\n')
            
    return True

if __name__ == "__main__":
    new_secret = generate_secret()
    if update_env(new_secret):
        print("Successfully generated new JWT_SECRET and updated .env")
        print("Note: ADMIN_TOKEN has been removed from .env as it's no longer needed for the API.")
    else:
        print("Failed to update .env")
