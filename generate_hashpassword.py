from passlib.hash import bcrypt

password = "adminuser123"  # Replace with your desired password
hashed_password = bcrypt.hash(password)
print(hashed_password)