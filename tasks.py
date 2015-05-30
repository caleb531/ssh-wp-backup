#!/usr/bin/env python3

import subprocess
from invoke import task


@task
def test():
    # invoke.run() does not color output, unfortunately
    nosetests = subprocess.Popen(['nosetests', '--rednose'])
    nosetests.wait()


@task
def cover():
    nosetests = subprocess.Popen(['nosetests', '--with-coverage',
                                  '--cover-erase', '--cover-html'])
    nosetests.wait()
