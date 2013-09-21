"""Get latest posts from Pinboard and create a new blog post."""

import collections
import cStringIO
import datetime
import os
import re
import sys

import gflags
import requests

FLAGS = gflags.FLAGS

gflags.DEFINE_string(
    'octopress', '.', 'location of octopress directory')
gflags.DEFINE_integer(
    'days', 7, 'number of days of bookmarks to request')
gflags.DEFINE_string(
    'token_file', '/Users/blanders/.pinboard', 'Pinboard API token file')

# Tags not to include in the HTML output, e.g. "blog this" markers
BAD_TAGS = frozenset(['@Blog'])

OUT_FILE = 'source/_posts/%s-link-dump-for-%s.markdown'

API = ('https://api.pinboard.in/v1/posts/all'
       '?auth_token=%s'
       '&format=json'
       '&fromdt=%s')

POST_TITLE = 'Link Dump for %s'

# A tag with this prefix is the "main topic" for the post, and will be used
# to create groupings in the HTML output.
MAIN_TOPIC_PREFIX = 'mt:'

HEADER = """---
layout: post
title: %s
date: %s
comments: false
categories: links
---"""

NOW = datetime.datetime.utcnow()
DATE = datetime.datetime.strftime(NOW, '%Y-%m-%d')
TIME = datetime.datetime.strftime(NOW, '%Y-%m-%d %H:%S')


def get_posts(days):
    """Download recent posts from Pinboard."""

    fromdt = datetime.datetime.strftime(
        NOW - datetime.timedelta(days=days),
        '%Y-%m-%dT%H:%M:%SZ')

    with open(FLAGS.token_file, 'r') as tfile:
        token = tfile.read().strip()

    return requests.post(API % (token, fromdt)).json()


def clean_up_posts(posts):
    """Clean up the raw JSON we get back from Pinboard."""

    parsed = []
    for post in posts:
        # Deal with Unicode fun
        for field in ['description', 'extended', 'tags']:
            post[field] = post[field].encode('ascii', 'ignore')

        # Skip private posts
        if post['shared'] != 'yes':
            continue

        # If there's no description, use the URL
        if not post['description']:
            post['description'] = post['href']

        # Clean up the extended text, if any. Skip whitespace-only content
        if re.search(r'^[\s\r\n]*$', post['extended']):
            post['extended'] = None
        else:
            post['extended'] = post['extended'].strip()

        # Extract and process the tags, including finding a "category" tag
        # which is denoted by a mt: prefix (for "main tag")
        tags = post['tags'].split()
        post['tags'] = []

        category = ''  # don't use None so we can use string methods later
        for tag in tags:
            if tag in BAD_TAGS:
                continue

            if tag.startswith(MAIN_TOPIC_PREFIX):
                category = tag.split(':', 2)[1].replace('_', ' ')
                continue

            post['tags'].append(tag)

        if category:
            post['category'] = category.title()
        elif post['tags']:
            post['category'] = post['tags'][0].replace('_', ' ').title()
        else:
            post['category'] = 'Misc'

        # If there's more than one tag, remove the category from the list if
        # it exists. If there's only one tag, leave it, even if it's the cat
        if len(post['tags']) > 1 and category in post['tags']:
            post['tags'].remove(category)

        parsed.append(post)
    return parsed


def sort_categories(categories):
    """Apply our special sort order (Misc is last) to the category list."""
    out = sorted(categories)
    if 'Misc' in out:
        out.remove('Misc')
        out.append('Misc')
    return out


def create_post(grouped):
    """Format the post into markdown."""
    categories = sort_categories(grouped.keys())

    post = cStringIO.StringIO()
    post.write(HEADER % (POST_TITLE % DATE, TIME))

    for category in categories:

        post.write('\n# %s\n\n' % category)

        for post in grouped[category]:
            post.write(
                '* [%s](%s)' % (
                    post['description'].strip(), post['href'].strip()))

            if post['extended']:
                post.write('<br>\nExtended: %s' % post['extended'])

            if post['tags']:
                post.write('<br>\n_Tags:_ %s' % ', '.join(post['tags']))

            post.write('\n')

    return post.getvalue()


def group_posts(parsed):
    """Take the raw list of posts and group them by categories."""
    grouped = collections.defaultdict(list)
    for post in parsed:
        grouped[post['category']].append(post)
    return grouped


def main(argv):
    """Main entry point for the application."""
    try:
        argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError, err:
        print '%s\\nUsage: %s ARGS\\n%s' % (err, sys.argv[0], FLAGS)
        sys.exit(1)

    posts = get_posts(FLAGS.days)
    parsed = clean_up_posts(posts)
    grouped = group_posts(parsed)

    outfile = os.path.join(FLAGS.octopress, OUT_FILE % (DATE, DATE))
    with open(outfile, 'w') as post:
        post.write(create_post(grouped))


if __name__ == '__main__':
    main(sys.argv)
