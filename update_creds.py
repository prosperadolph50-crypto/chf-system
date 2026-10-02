import os
file_path = r'c:\Users\USER\Desktop\CHF JOINED DATA\backend\main.py'
with open(file_path, 'r') as f:
    content = f.read()

content = content.replace('if username == "admin" and password == "12345":', 'if username == "prosper.kashaga" and password == "Ruthmsechu@822":')

with open(file_path, 'w') as f:
    f.write(content)
