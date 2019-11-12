#!/usr/bin/env python

'''
tag_generator.py
Copyright 2017 Long Qian
Contact: lqian8@jhu.edu
This script creates tags for your Jekyll blog hosted by Github page.
No plugins required.
'''

import glob
import os


def tag_generator(post_dir, tag_dir):
    filenames = glob.glob(post_dir + '*md')

    total_tags = []
    for filename in filenames:
        print(f'filename: {filename}')
        f = open(filename, 'r')
        crawl = False
        for line in f:
            if crawl:
                current_tags = line.strip().split()
                if current_tags[0] == 'tags:':
                    total_tags.extend(current_tags[1:])
                    crawl = False
                    break
            if line.strip() == '---':
                if not crawl:
                    crawl = True
                else:
                    crawl = False
                    break
        f.close()
    total_tags = set(total_tags)

    old_tags = glob.glob(tag_dir + '*.md')
    for tag in old_tags:
        os.remove(tag)
        
    if not os.path.exists(tag_dir):
        os.makedirs(tag_dir)

    for tag in total_tags:
        tag_filename = tag_dir + tag + '.md'
        f = open(tag_filename, 'a')
        write_str = f'---\nlayout: tagpage\ntitle: \"Tag: {tag}\"\ntag: {tag}\nrobots: noindex\n---\n'
        f.write(write_str)
        f.close()

    return len(total_tags)


if __name__ == '__main__':
    total_tag_count = tag_generator('_posts/', 'tag/')
    print(f'Tags generated, count {total_tag_count}')
