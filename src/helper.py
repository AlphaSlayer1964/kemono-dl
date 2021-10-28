import os
import datetime
import re

from .arguments import get_args

args = get_args()

def check_post_archived(post):
    if args['archive']:
        if os.path.exists(args['archive']):
            with open(args['archive'],'r') as f:
                archived = f.read().splitlines()

            if '/{service}/user/{user}/post/{id}'.format(**post) in archived:
                return False
    return True


def check_date(date):
    if not args['date'] and not args['datebefore'] and not args['dateafter']:
        return True

    if date == datetime.datetime.min:
        return False

    if not args['datebefore']:
        args['datebefore'] = datetime.datetime.min

    if not args['dateafter']:
        args['dateafter'] = datetime.datetime.max

    if not args['date']:
        args['date'] = datetime.datetime.min

    if date == args['date'] or date <= args['datebefore'] or date >= args['dateafter']:
        return True
    return False


def check_size(size):
    if not args['min_filesize'] and not args['max_filesize']:
        return True

    if size == 0:
        return False

    if not args['min_filesize']:
        args['min_filesize'] = '0'

    if not args['max_filesize']:
        args['max_filesize'] = 'inf'

    if int(size) <= float(args['max_filesize']) and int(size) >= int(args['min_filesize']):
        return True
    return False

def check_extention(file_name):
    file_extention = file_name.split('.')[-1]

    for valid_extention in args['only_filetypes']:
        if valid_extention == file_extention.lower():
            return True
        print('Skiping "{}"'.format(file_name))
        return False

    for invalid_extention in args['skip_filetypes']:
        if invalid_extention == file_extention.lower():
            print('Skiping "{}"'.format(file_name))
            return False
        return True

    return True


def win_file_name(file_name):
    file_name = file_name.rsplit('.', 1) # separate extention
    if len(file_name) == 2:
        if len(file_name[1]) > 10: # if the extention is longer than 10 char assume it is not an extention
            file_name[0] = file_name[0] + '.' + file_name[1]
            file_name.remove(file_name[1])
    file_name[0] = re.sub(r'[\n\t]+',' ', file_name[0]) # convert newline and tabs to white space
    file_name[0] = re.sub(r'[\\/:\"*?<>|]+','', file_name[0]) # remove illgal file name characters
    if len(file_name) == 2:
        file_name[0] = file_name[0][:260-len(file_name[1])-1]
        return file_name[0] + '.' + file_name[1]
    else:
        file_name[0] = file_name[0][:260] # if file name some how has no extention
        return file_name[0]

def win_folder_name(folder_name):
    folder_name = re.sub(r'[\n\t]+',' ', folder_name) # convert newline and tabs to white space
    folder_name = re.sub(r'[\\/:\"*?<>|]+','', folder_name) # remove illgal file name characters
    folder_name = folder_name[:248]
    folder_name = folder_name.strip('. ') # windows will remove trailing periods
    return folder_name


def add_indexing(index, file_name, list):
    if len(list) < 10:
        return '[{:01d}]_{}'.format(index+1, file_name)
    elif len(list) < 100:
        return '[{:02d}]_{}'.format(index+1, file_name)
    elif len(list) < 1000: # there is no way a post has more than 1000 attachments!
        return '[{:03d}]_{}'.format(index+1, file_name)