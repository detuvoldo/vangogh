#!/usr/bin/python

# download_images_from_csv.py
# Copyright (C) 2016
#   Guilherme Folego (gfolego@gmail.com)
#   Otavio Gomes (otaviolmiro@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
============================================================
Download images from CSV
============================================================

Download images from a CSV file

"""


import sys
import os.path
import argparse
import csv
import urllib2
import hashlib
from progressbar import ProgressBar, Percentage, Bar, \
        AdaptiveETA, AdaptiveTransferSpeed
from hurry.filesize import size, alternative
from common import set_verbose_level, print_verbose, dir_type


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-c', '--csv', type=argparse.FileType('r'), required=True,
            help='csv file')
    parser.add_argument('-d', '--directory', type=dir_type, required=True,
            help='destination directory')
    parser.add_argument('-v', '--verbose', action='count',
            help='verbosity level')

    args = parser.parse_args(args=argv)
    return args

# Parse page entry
def parse_entry(dest_dir, page,
        idx_pageid, idx_imageurl, idx_sha1):

    # Get values
    pageid = page[idx_pageid]
    image_url = page[idx_imageurl]
    image_sha1 = page[idx_sha1]

    # Parse
    file_extension = os.path.splitext(image_url)[1]
    image_path = os.path.join(dest_dir, pageid + file_extension)

    return image_path, image_url, image_sha1

# Download image
def download_image(img_path, img_url):

    # Fetch URL
    url = urllib2.urlopen(img_url)
    meta = url.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print_verbose("Downloading image %s (%s)" % (url.geturl(),
        size(file_size, system=alternative)), 0)

    # Set progress bar
    widgets = ['Progress: ', Percentage(), ' ', Bar(),
            ' ', AdaptiveETA(), ' ', AdaptiveTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=file_size).start()

    # Download
    f = open(img_path, 'wb')
    file_size_dl = 0
    block_sz = 1024 * 8

    while True:
        buff = url.read(block_sz)
        if not buff:
            break

        file_size_dl += len(buff)
        f.write(buff)
        pbar.update(file_size_dl)

    # Done
    f.close()
    pbar.finish()
    return url.getcode()

# Check SHA1
def check_sha1(img_path, img_sha1):
    sha1 = hashlib.sha1()
    with open(img_path, 'rb') as f:
        sha1.update(f.read())

    if (img_sha1 != sha1.hexdigest()):
        raise ValueError("File '%s' SHA1 digest does not match" % img_path)
    return True

# Read CSV and download images
def download_from_csv(csvfile, dest_dir):

    # Define writer
    reader = csv.reader(csvfile, quoting=csv.QUOTE_ALL, strict=True)

    # Field names
    field_names = reader.next()

    # Indices
    idx_pageid = field_names.index('PageID')
    idx_imageurl = field_names.index('ImageURL')
    idx_sha1 = field_names.index('ImageSHA1')

    # For each page entry
    for page in reader:

        # Parse entry
        img_path, img_url, img_sha1 = parse_entry(dest_dir, page,
                idx_pageid, idx_imageurl, idx_sha1)

        # Download only if image does not exist
        if (not os.access(img_path, os.R_OK)):
            download_image(img_path, img_url)

        # Check SHA1
        check_sha1(img_path, img_sha1)


# Main
def main(argv):

    # Parse arguments
    args = parse_args(argv)
    set_verbose_level(args.verbose)

    print_verbose("Args: %s" % str(args), 1)

    # Download images
    download_from_csv(args.csv, args.directory)


if __name__ == "__main__":
    main(sys.argv[1:])

