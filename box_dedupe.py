#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 17:57:33 2019

@author: johnlin
"""

FOLDER_ID = '68995521097' # Replace with the folder ID you want to deduplicate. 0 for root (All Files).

from boxsdk import Client
from collections import defaultdict
import datetime
from boxsdk.exception import BoxAPIException
from auth import authenticate

def get_all_items(folder, types={'file','folder'}):
    items = list(folder.get_items(sort='name'))
    
    i = 0
    while i < len(items):
        if items[i]['type'] == 'folder':
            temp = list(items[i].get_items(sort='name'))
            if(len(temp)) > 0:
                items = items + temp
        i +=1
    items = [i for i in items if i.type in types]
    return items
 
def find_dup_folders(items):
    folder_names = []
    folders = []
    for x in items:
        if x.type == 'folder':
            folders.append(x)
            folder_names.append(x.name)
    dups = [folders[i] for i in [i for i, x in enumerate(folder_names) if folder_names.count(x) > 1]]
    
    dup_paths = []
    for x in dups:
        path = x.get()['path_collection']['entries']
        path.append(x.name)
        path = tuple(path)
        dup_paths.append(path)
        
    true_dups = [dups[i] for i in [i for i, x in enumerate(dup_paths) if dup_paths.count(x) > 1]]
    true_dups_paths = [dup_paths[i] for i in [i for i, x in enumerate(dup_paths) if dup_paths.count(x) > 1]]

    dup_path_groups = list_duplicates(true_dups_paths)
    dup_path_groups.sort(key = lambda x:len(x[0]), reverse=True)
    
    dups_grouped = []
    for x in dup_path_groups:
        dups_grouped.append([true_dups[i] for i in x[1]])
    return dups_grouped
        
def list_duplicates(seq):
    tally = defaultdict(list)
    for i,item in enumerate(seq):
        tally[item].append(i)
    return [(key,locs) for key,locs in tally.items() if len(locs)>1]

auth,_,_ = authenticate()
client = Client(auth)

root_folder = client.folder(FOLDER_ID).get()

print('Getting all items in {0}'.format(root_folder))
items = get_all_items(root_folder, {'folder'})
print('Finding duplicates in {0}'.format(root_folder))
dups = find_dup_folders(items)
print('{0} duplicates found.'.format(len(dups)))
print(dups)

for dup_pair in dups:
    print('Processing duplicate pair {0}'.format(dup_pair))
    for i in range(1,len(dup_pair)):
        folder_items = get_all_items(dup_pair[i].get())
        folder_folders = [i for i in folder_items if i.type == 'folder']
        folder_files = [i for i in folder_items if i.type == 'file']
        
        for x in folder_folders:
            x = x.get()
            if x['item_collection']['total_count'] == 0:
                path = x['path_collection']['entries']
                path = path[path.index(dup_pair[i])+1::]
                
                current_folder = dup_pair[0]
                for path_ in path:
                    current_folder_items = list(current_folder.get_items(sort='name'))
                    current_folder_folders = [i for i in current_folder_items if i.type == 'folder']
                    next_folder = next((x for x in current_folder_folders if x.name == path_.name), None)
                    if next_folder == None:
                        try:
                            next_folder = current_folder.create_subfolder(path_.name)
                        except BoxAPIException as e:
                            if e.context_info['conflicts'][0]['type'] == 'file':
                                conflict_file = client.file(e.context_info['conflicts'][0]['id']).get()
                                conflict_file.update_info({'name': conflict_file.name + '.dPa' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
                                next_folder = current_folder.create_subfolder(path_.name)
                                print('{0} renamed because it conflicted with path.'.format(conflict_file))
                            else:
                                raise Exception('Something went wrong.')
                    current_folder = next_folder
                current_folder_items = list(current_folder.get_items(sort='name'))
                y = next((temp for temp in current_folder_items if temp.name == x.name), None)
                if y == None:
                    x.move(current_folder)
                    print('Empty folder {0} move to {1}'.format(x, current_folder))
                else:
                    if y.type == 'folder':
                        x.delete()
                        print('Empty folder {0} exists at destination. Delete.'.format(x))
                    elif y.type == 'file':
                        x = x.update_info({'name': x.name + '.dFi' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
                        x.move(current_folder)
                        print('Empty folder {0} name conflicts with file at destination. Rename and move to {1}.'.format(x, current_folder))
                        
        for x in folder_files:
            path = x.get()['path_collection']['entries']
            path = path[path.index(dup_pair[i])+1::]
            
            current_folder = dup_pair[0]
            for path_ in path:
                current_folder_items = list(current_folder.get_items(sort='name'))
                current_folder_folders = [i for i in current_folder_items if i.type == 'folder']
                next_folder = next((x for x in current_folder_folders if x.name == path_.name), None)
                if next_folder == None:
                    try:
                        next_folder = current_folder.create_subfolder(path_.name)
                    except BoxAPIException as e:
                        if e.context_info['conflicts'][0]['type'] == 'file':
                            conflict_file = client.file(e.context_info['conflicts'][0]['id']).get()
                            conflict_file.update_info({'name': conflict_file.name + '.dPa' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
                            next_folder = current_folder.create_subfolder(path_.name)
                            print('{0} renamed because it conflicted with path.'.format(conflict_file))
                        else:
                            raise Exception('Something went wrong.')
                current_folder = next_folder
            current_folder_items = list(current_folder.get_items(sort='name'))
            y = next((temp for temp in current_folder_items if temp.name == x.name), None)
            if y == None:
                x.move(current_folder)
                print('File {0} move to {1}'.format(x, current_folder))
            else: 
                if y.type == 'folder':
                    x = x.update_info({'name': x.name + '.dFo' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
                    x.move(current_folder)
                    print('File {0} name conflicts with folder at destination. Rename and move to {1}.'.format(x, current_folder))
                elif y.type == 'file':
                    if y.sha1 == x.sha1:
                        x.delete()
                        print('File {0} exists with same name and SHA1 at destination. Delete'.format(x))
                    else: 
                        x = x.update_info({'name': x.name + '.d' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))})
                        x.move(current_folder)
                        print('File {0} exists with same name but different SHA1 at destination. Rename and move to {1}'.format(x, current_folder))
                        
        if len(get_all_items(dup_pair[i].get(), {'file'})) == 0:
            dup_pair[i].delete()
        else:
            raise Exception('Something went wrong. Files remain.')
                     