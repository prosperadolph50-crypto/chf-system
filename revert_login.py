import os
import shutil

file_path = r'c:\Users\USER\Desktop\CHF JOINED DATA\frontend\index.html'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Strip out login logic dynamically instead of exact matching strings
import re
content = re.sub(r'// Login states.*?const handleLogout = \(\) => {.*?};', '', content, flags=re.DOTALL)
content = re.sub(r'if \(!isLoggedIn\).*?return \(.*?</form>.*?</div>.*?</div>.*?.*?}', '', content, flags=re.DOTALL)

# Revert Header
header_with_logout = r'<div className="flex justify-between items-center bg-white p-4 rounded-lg shadow mb-4">.*?<h1 className="text-3xl font-bold text-blue-600">CHF Members System</h1>.*?<button onClick={handleLogout}.*?</div>'
original_header = '<h1 className="text-3xl font-bold mb-6 text-center text-blue-600">CHF Members System</h1>'
content = re.sub(header_with_logout, original_header, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

# 2. Re-zip
folder_to_zip = 'c:/Users/USER/Desktop/CHF JOINED DATA'
output_filename = 'c:/Users/USER/Desktop/Mfumo_Wa_CHF'
shutil.make_archive(output_filename, 'zip', folder_to_zip)
print('Reverted and Zipped!')
