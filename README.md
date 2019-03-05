# box_dedupe
box_dedupe deduplicates folders and files in Box with same name. 

# Motivation
Uploading files using Box via FTP is a common way to bulk transfer files to Box. When using multiple FTP transfers, a race condition can occur resulting in duplicated folder names. Content will be split between the folders with the same names. This creates difficulties in accessing files through FTP (as only one duplicated folder can be stepped into) and general confusion as duplicate names is not allowed typically. box_dedupe aims to deduplicate and combine the folders. 

# Usage
1. Install `boxsdk` and `bottle`.   
```python
pip install boxsdk bottle
```
2. Register app on Box and `config_oauth.py` containing id and secret.  
```python
client_id = 'YOUR ID'
client_secret = 'YOUR SECRET'
```
3. Edit box_dedupe.py `FOLDER_ID` with desired starting directory. Use 0 for `All Files`. 

# Renames
Files or folders will be renamed in some circumstances. The following prefixes are used:  
* `.dYYYY-MM-DD HH:MM:SS` - when moving a file, file with same name exists at destination but different SHA1. File is renamed and moved.
* `.dFoYYYY-MM-DD HH:MM:SS` - when moving a file, folder with same name exists at destination. File is renamed and moved.
* `.dFiYYYY-MM-DD HH:MM:SS` - when moving an empty folder, file with same name exists at destination. Folder is renamed and moved.
* `.dPaYYYY-MM-DD HH:MM:SS` - when traversing a folder structure, file exists with the same name as needed for correct folder structure. Conflicting file is renamed and needed subfolder to continue traversing is created.

# Credits
OAuth2 authentication code is based off of [box/box-python-sdk](https://github.com/box/box-python-sdk)'s example code.
