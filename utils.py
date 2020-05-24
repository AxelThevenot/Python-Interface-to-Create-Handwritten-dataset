import os
import json
import glob

def get_json(file_name):
    # open en return the content of JSON file as a dictionary
    with open(file_name) as json_file:
        json_data = json.load(json_file)
    return json_data

def check_folder_path(path):
    # create a folder if not exists
    if not os.path.exists(path):
        os.mkdir(path)

def order_filename_by_prefix(prefix, zfill=5):
    # get all the file names with the pattern
    file_names = glob.glob(prefix + '*')
    file_names = sorted(file_names)

    # if exists
    n_done = len(file_names)
    if n_done:
        # rename each sample incremented one by one its id number
        for i, file_name in enumerate(file_names):

            extension = file_name.split('.')[-1]
            str_number = str(i).zfill(zfill)
            # use _tmp_ to avoid override an existing file
            renamed = f'{prefix}_tmp_{str_number}.{extension}'
            os.rename(file_name, renamed)

        # remove the _tmp_
        tmp_names = glob.glob(prefix + '_tmp_*')
        for i, tmp_name in enumerate(tmp_names):
            os.rename(tmp_name, tmp_name.replace('_tmp_', ''))
    return n_done
