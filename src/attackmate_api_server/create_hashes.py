from passlib.context import CryptContext
import json

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

# Define your users here: { 'username': 'plain_text_password' }
users = {
    'testuser': 'testuser',
    'admin': 'change_me_immediately',
    'analyst': 'secure_password_123'
}

hashed_users = {username: pwd_context.hash(password) for username, password in users.items()}

print("\n--- Copy the line below into your .env file ---")
print("# AttackMate API User Credentials")
print(f"USERS='{json.dumps(hashed_users)}'")
print("\n--- End of Environment Variables ---")
