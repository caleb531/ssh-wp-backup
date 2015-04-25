#!/usr/bin/env python

import os
import os.path
import glob
import sys
import re

program_dir = sys.argv[1]
local_backup_patt = sys.argv[2]
max_local_backups = int(sys.argv[3])

if not os.path.isdir(local_backup_patt):

    # Convert date format sequences to wildcards
    local_backup_patt = re.sub('%[A-Za-z]', '*', local_backup_patt)
    # Expand ~ to home folder for local backup pattern
    local_backup_patt = os.path.expanduser(local_backup_patt)

    # Retrieve list of local backups sorted from oldest to newest
    local_backups = sorted(glob.iglob(local_backup_patt),
                           key=lambda path: os.stat(path).st_mtime)
    backups_to_purge = local_backups[:-max_local_backups]

    for backup in backups_to_purge:
        os.remove(backup)
