#!/usr/bin/env python3

import os
import subprocess
from invoke import task


@task
def test():
    # invoke.run() does not respect colored output, unfortunately
    nosetests = subprocess.Popen(['nosetests', '--rednose'])
    nosetests.wait()


@task
def cover():
    try:
        os.mkdir('cover')
    except OSError:
        pass
    nosetests = subprocess.Popen(['nosetests', '--with-coverage',
                                  '--cover-erase', '--cover-html'])
    nosetests.wait()
