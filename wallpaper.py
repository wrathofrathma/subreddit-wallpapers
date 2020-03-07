#!/usr/bin/python3

import praw
import re
from urllib import request
import pathlib
import shutil
from time import sleep
from os import system
import string
import numpy as np
from PIL import Image

# Config
prefs = {
    "user_agent": "wallpaper_engine",
    "client_id": "your_id_here",
    "client_secret": "your_secret_here",
    "aspect_ratio": (16, 9),
    "search_limit": 100,
    "download_limit": 20,
    "subreddits": ["Animewallpaper",],
    "criteria": "top",
    "time_filter": "week",  # can be all, day, hour, month, week
    "allow_nsfw": True,
    "wallpaper_directory": str(pathlib.Path.home()) + "/.wallpapers",
    "sleep": 60 * 30,
}


aspect_ratios = {
    (16, 9): [(1920, 1080), (2560, 1440), (3840, 2160)],
    (21, 9): [(2560, 1080), (3440, 1440)],
}


def check_res(title, res_dict):
    for k, v in res_dict.items():
        for res in v:
            results = re.search(res, title)
            if results is not None:
                return k
    return None


def filter_urls(entries, prefs):
    # Generate our list of resolutions -> regex strings for our aspect ratio
    res_regex = {}
    ar = prefs["aspect_ratio"]
    for res in aspect_ratios[ar]:
        res_regex[res] = []
        res_regex[res] += [str(res[0]) + "x" + str(res[1])]
        res_regex[res] += [str(res[0]) + " x " + str(res[1])]

    urls = []
    for entry in entries:
        submission = r.submission(id=entry)
        title = submission.title
        if check_res(title, res_regex) is not None:
            if prefs["allow_nsfw"] is False and submission.over_18 is False:
                urls += [(title, submission.url)]

            elif prefs["allow_nsfw"] is True:
                urls += [(title, submission.url)]
    return urls


def download_images(url_list, prefs):
    wp_dir = prefs["wallpaper_directory"]
    # Removing the old directory
    try:
        shutil.rmtree(wp_dir)
    except FileNotFoundError:
        pass

    # Creating a new directory
    pathlib.Path(wp_dir).mkdir(parents=True, exist_ok=True)

    count = 0
    path_list = []
    # Download all .jpg & png files.
    for title, url in url_list:
        if url.endswith("jpg") or url.endswith("png"):
            count += 1
            title = str(title)
            rm_punctuation = dict((ord(char), None) for char in string.punctuation)
            title = title.translate(rm_punctuation)

            path = wp_dir + "/" + title + url[-4:]
            path_list += [path]
            request.urlretrieve(url, path)
            if count >= prefs["download_limit"]:
                return path_list
    return path_list
    # TODO - Add support for imgur albums and jpeg files.


def get_entries(prefs):
    entries = []
    for sub in prefs["subreddits"]:
        s = r.subreddit(sub)
        if prefs["criteria"] == "top":
            entries += [
                str(x) for x in s.top(prefs["time_filter"], limit=prefs["search_limit"])
            ]

        elif prefs["criteria"] == "hot":
            entries += [str(x) for x in s.hot(limit=prefs["search_limit"])]
    return entries


def set_background(bg):
    cmd = "gsettings set org.gnome.desktop.background picture-uri 'file://" + bg + "'"
    print(cmd)
    system(cmd)
    system("gsettings set org.gnome.desktop.background picture-options 'scaled'")


if __name__ == "__main__":
    r = praw.Reddit(
        user_agent="wallpaper_engine",
        client_id=prefs["client_id"],
        client_secret=prefs["client_secret"],
    )

    while True:
        # Refresh our image cache
        entries = get_entries(prefs)
        urls = filter_urls(entries, prefs)
        wallpapers = download_images(urls, prefs)
        n_wallpapers = len(wallpapers)
        order = np.arange(n_wallpapers)
        np.random.shuffle(order)
        for wp in order:
            path = wallpapers[wp]
            img = Image.open(path)
            # Checks if it was mislabeled
            if img.size not in aspect_ratios[prefs["aspect_ratio"]]:
                img.close()
                continue
            set_background(wallpapers[wp])
            sleep(prefs["sleep"])
