#!/usr/bin/env python3

import subprocess
from invoke import task


@task
def test():
    # invoke.run() does not color output, unfortunately
    nosetests = subprocess.Popen(['nosetests-3.4', '--rednose'])
    nosetests.wait()


@task
def cover():
    nosetests = subprocess.Popen(['nosetests-3.4', '--with-coverage',
                                  '--cover-erase', '--cover-html'])
    nosetests.wait()
