"""Script for downloading videos from gdrive and dropbox; it's not perfect but does part of the job."""
import sys
import os
import os.path as osp
import shutil
import pandas as pd
import requests
import tqdm
import filetype
import re

CMT_ID = 'CMT ID'
VIDEO_LINK = 'Link to the video'
DEST = 'videos'
GDRIVE_URL = 'https://docs.google.com/uc?export=download'


def _download_from_gdrive(file_id, destination):

    session = requests.Session()

    params = dict(id=file_id)
    response = session.get(GDRIVE_URL, params=params, stream=True)
    token = _get_confirm_token(response)

    if token:
        params['confirm'] = token
        response = session.get(GDRIVE_URL, params=params, stream=True)

    _save_response_content(response, destination)    

def _get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def _download_from_dropbox(link, destination):

    session = requests.Session()

    headers = {'user-agent': 'Wget/1.16 (linux-gnu)'}
    response = session.get(link, headers=headers, stream=True)
    _save_response_content(response, destination)    


def _save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in tqdm.tqdm(response.iter_content(CHUNK_SIZE)):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


_gdrive_link_pattern = re.compile(r'(.*?)(/view.*|/edit.*|$).*')


def download_from_gdrive(link):
    link = _gdrive_link_pattern.match(link).groups()[0]

    file_id = link.split('/')[-1]
    filename = 'gdrive_file'
    _download_from_gdrive(file_id, filename)
    return filename


def download_from_dropbox(link):
    filename = 'dropbox_file'
    #dropbox.sharing_get_shared_link_file_to_file(filename, link)

    _download_from_dropbox(link, filename)
    return filename


def download_generic(link):
    raise NotImplementedError


def download_file(link):
    if 'google' in link:
        return download_from_gdrive(link)
    elif 'dropbox' in link:
        return download_from_dropbox(link)
    else:
        return download_generic(link)


def main(filename):

    df = pd.read_csv(filename)
    if not osp.exists(DEST):
        os.mkdir(DEST)

    existing_vids = set([int(osp.splitext(f)[0]) for f in os.listdir(DEST) if '.' in f])
    print(existing_vids)
    n_videos = len(df)
    print(f'Processing {n_videos} files')
    for i, (cmt_id, vid_link) in enumerate(zip(df[CMT_ID], df[VIDEO_LINK])):

        if cmt_id in existing_vids:
            print(f'Video #{cmt_id} already exists. Skipping.')
            continue 

        print(f'Downloading video ID={cmt_id:02d} [{i+1}/{n_videos}].')
        try:
            downloaded_file = download_file(vid_link)
        except:
            print(f'Couldn\'t download file from "{link}".')
        else:
            try:
                ext = filetype.guess(downloaded_file)
                ext = '' if ext is None else '.' + ext.extension
                target_filename = osp.join(DEST, f'{cmt_id}{ext}')
                shutil.move(downloaded_file, target_filename)
            except Exception as err:
                print(err)
                print(f'Skipping cmt_id #{cmt_id}.')


if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)

    #print(download_from_gdrive('https://drive.google.com/file/d/1DhBvBblixq7kXnq6pUrcA_Q7msBlFVz0/view'))
    #print(download_from_dropbox('https://www.dropbox.com/s/prbu9uhdr0w2tcs/OOL_2020.mp4?dl=0'))
