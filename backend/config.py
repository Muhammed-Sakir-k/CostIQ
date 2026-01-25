from werkzeug.security import generate_password_hash

ADMIN_USERNAME = "admin"

# Generate once, then keep it fixed
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")