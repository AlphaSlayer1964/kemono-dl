import os
import datetime
import re
import json

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

def check_post_edited(post, post_path):
    if args['update']:
        json_path = os.path.join(post_path,'{id}.json'.format(**post))
        if not os.path.exists(json_path):
            return False
        current_edited = datetime.datetime.strptime(post['edited'], r'%a, %d %b %Y %H:%M:%S %Z') if post['edited'] else datetime.datetime.min
        with open(json_path,'r') as f:
            data = json.loads(f.read())
        recorded_edited = datetime.datetime.strptime(data['edited'], r'%a, %d %b %Y %H:%M:%S %Z') if data['edited'] else datetime.datetime.min
        if current_edited <= recorded_edited:
            return False
    return True

def check_date(date):
    if args['date'] == datetime.datetime.min and args['datebefore'] == datetime.datetime.min and args['dateafter'] == datetime.datetime.max:
        return True

    if date == datetime.datetime.min:
        return False

    if date == args['date'] or date <= args['datebefore'] or date >= args['dateafter']:
        return True
    return False


def check_size(size):
    if args['min_filesize'] == '0' and args['max_filesize'] == 'inf':
        return True

    if size == 0:
        return False

    if int(size) <= float(args['max_filesize']) and int(size) >= int(args['min_filesize']):
        return True
    return False

def check_extention(file_name):
    file_extention = file_name.split('.')[-1]

    if args['only_filetypes']:
        if not file_extention.lower() in args['only_filetypes']:
            print('[info] Wrong file type skiping download for "{}"'.format(file_name))
            return False

    if args['skip_filetypes']:
        if file_extention.lower() in args['skip_filetypes']:
            print('[info] Wrong file type skiping download for "{}"'.format(file_name))
            return False

    return True

# If am imgur link is embedded an attachmanet and post file are created that are the thumbanil
# image of the video. The problem is the api saves these files names as the image link.
def win_file_name(file_name):
    # separate extention
    file_name = file_name.rsplit('.', 1)
    # convert newline and tabs to white space
    file_name[0] = re.sub(r'[\n\t]+',' ', file_name[0])
    # remove illgal file name characters
    file_name[0] = re.sub(r'[\\/:\"*?<>|]+','', file_name[0])
    if len(file_name) == 2:
        # incase file name has a period but no extention
        # convert newline and tabs to white space
        file_name[1] = re.sub(r'[\n\t]+',' ', file_name[1])
        # remove illgal file name characters
        file_name[1] = re.sub(r'[\\/:\"*?<>|]+','', file_name[1])
        file_name[0] = file_name[0][:260-len(file_name[1])-1]
        return file_name[0] + '.' + file_name[1]
    else:
        # if file name some how has no extention
        file_name[0] = file_name[0][:260]
        return file_name[0]


def win_folder_name(folder_name):
    # convert newline and tabs to white space
    folder_name = re.sub(r'[\n\t]+',' ', folder_name)
    # remove illgal file name characters
    folder_name = re.sub(r'[\\/:\"*?<>|]+','', folder_name)
    folder_name = folder_name[:248]
    # windows will remove trailing periods and white spaces
    folder_name = folder_name.strip('. ')
    return folder_name


def add_indexing(index, file_name, list):
    index_string = str(index+1).zfill(len(str(len(list))))
    return '[{}]_{}'.format(index_string, file_name)

def compare_hash(file_name, hash):
    import hashlib

    sha256_hash = hashlib.sha256()
    with open(file_name,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)

    if hash.lower() == sha256_hash.hexdigest().lower():
        return True
    return False