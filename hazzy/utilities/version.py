#!/usr/bin/env python

import os
import subprocess

from utilities import logger
log = logger.get(__name__)

repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

VERSION = None
VERSION_URL = None

# Check if we are running in a git repo
if os.path.exists(os.path.join(repo_dir, '.git')):

    log.info('Running from a git repository ...')

    # This is a git repo, so get some data
    try:

        # Determing the branch name we are running from
        branch = subprocess.check_output(['git', 'rev-parse',
                                                  '--abbrev-ref',
                                                  'HEAD'],
                                                 cwd=repo_dir)

        # Get some info, tag, commit hash, repo state etc.
        discription = subprocess.check_output(["git", "describe",
                                                "--always", "--dirty",
                                                "--tags", "--match",
                                                "v*"], 
                                                cwd=repo_dir)

        # Typical git describe output
        #    Ex. v0.1.0-402-gcb833e6-dirty
        # If no tag was found, will just contain the commit hash
        #    Ex. cb833e6
        # If clean version it will just have the tag
        #    Ex. v0.1.0

        # Split description into list
        info = discription.strip().split('-')

        commit_hash = None

        # If length is 1 it is either a clean version or commit hash
        if len(info) == 1:

            # If version the first letter will always be a "v"
            # The hash could beginning with a "v" too, but unlikely ...
            if info[0].startswith('v'):
                # Its a version tag number
                VERSION = info[0]

                # We can have enough info for a full url
                VERSION_URL = 'https://github.com/KurtJacobson/hazzy/tree/{}' \
                    .format(VERSION)

            else:
                # It is a commit hash
                commit_hash = info[0]
                VERSION = 'Commit hash: ' + commit_hash

        # Length is greater than 1, so we have more data
        else:

            # Add the branch name to the version Ex. v0.1.0~master
            info[0] += '~' + branch.strip()

            # Join together any additional information and format
            VERSION = '-'.join(info).replace('-', '.')

            # The commit hash is prefixed with a "g" to indicate is is a git hash
            # We need to remove is for use in the url
            commit_hash = info[2].lstrip('g')

        # If there is a commit hash make a url
        if commit_hash:
            VERSION_URL = 'https://github.com/KurtJacobson/hazzy/tree/{}' \
                .format(commit_hash)

    except subprocess.CalledProcessError:
        # So, git failed to give us a version number
        log.erro("Could not determine version info from git repo, is git installed?")

if not VERSION:

    # This is not a git repo, or git failed us, so read VERSION file
    version_file = os.path.join(repo_dir, 'VERSION')

    with open(version_file, 'r') as fh:
        VERSION = fh.readline().strip()

        if '~pre' in VERSION:
            # It is a pre release so no tag yet on github, use master
            VERSION_URL = 'https://github.com/KurtJacobson/hazzy'

        else:
            # It is a release so make a url to the version tag
            VERSION_URL = 'https://github.com/KurtJacobson/hazzy/tree/{}' \
                .format('v' + VERSION)

log.info(VERSION)
log.info(VERSION_URL)
