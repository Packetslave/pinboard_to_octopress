pinboard_to_octopress
=====================

Get bookmarks from Pinboard and create an Octopress post

Requirements:

* [python-gflags](https://code.google.com/p/python-gflags/)
* [requests](http://python-requests.org)

How to use:

* get your Pinboard API token (https://pinboard.in/settings/password)
* save it to a file somewhere secure. Make sure to set sane file permissions.
* either edit p20.py to point to your token file, or use the --token_file flag
* run p2o.py from your octopress directory, or use the --octopress flag
* your new post is ready to preview and publish!

By default, p2o will retrieve the last 7 days of posts. This can be overriden
with the --days flags.

p2o will only publish bookmarks that are public (*not* marked private)
