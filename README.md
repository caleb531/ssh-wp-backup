# SSH WordPress Backup

*Copyright 2015 Caleb Evans*  
*Released under the MIT license*

[![Build Status](https://travis-ci.org/caleb531/ssh-wp-backup.svg?branch=master)](https://travis-ci.org/caleb531/ssh-wp-backup)
[![Coverage Status](https://coveralls.io/repos/caleb531/ssh-wp-backup/badge.svg?branch=master)](https://coveralls.io/r/caleb531/ssh-wp-backup?branch=master)

SSH WordPress Backup is a command line utility for creating and restoring local
backups of a remote WordPress database via SSH.

## Getting Started

### Requirements

This utility assumes that you have (or have access to) the following:

- A Linux server with support for SSH
- SSH access to said server
- A WordPress installation on said server
- The `mysql` and `mysqldump` utilities installed on said server
- Python 3 installed on both the local and remote systems
	- Why? Because [Python 3 is *better*](https://docs.python.org/3/whatsnew/3.0.html)

### Configuring SSH

If you have not yet configured SSH key-based authentication on your server,
please follow the steps outlined in [this
article](http://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id/).

### Configuration files

This command line utility requires a single argument: the path to a
specially-formatted configuration file. This configuration file *must* have the
`.ini` extension and *must* contain the following properties (except those
properties marked as optional):

#### [paths]

- `wordpress`: the absolute path to the directory for the remote WordPress site
	- *e.g.* `~/public_html/mysite`
- `remote_backup`: the absolute path to the database backup file to be created
	- the path may include [date format sequences](http://strftime.org/)
		such as `%Y`
	- the utility will automatically create intermediate directories apart of
		the path if they do not exist
	- *e.g.* `~/backups/mysitedb-%Y-%m-%d.sql.gz`
- `local_backup`: the absolute path to the local backup file to be created
	- the path may also include date format sequences
	- like `remote_backup`, the utility will also create intermediate
		directories if they do not exist
	- *e.g.* `~/Documents/Backups/%Y-%m-%d/mysitedb-%H-%M-%S.sql.gz`

#### [ssh]

- `user`: the name of the user under which to log in
- `hostname`: the hostname or IP address used to connect.
- `port`: the port number used to connect

#### [backup]

- `compressor`: the shell command used for compressing the
	database backup on the server
	- if you specify this option, you must ensure that the file extensions for
		`paths.remote_backup` and `paths.local_backup` match that of the chosen
		compressor
	- *e.g.* `gzip`, `bzip2`, `gzip --best`, `bzip -v`
- `decompressor`: the shell command used for decompressing the backup
	when restoring from backup
	- if this option is present, the `compressor` option must also be present
		(and vice-versa)
	- *e.g.* `gzip -d`, `bzip2 -d`
- `max_local_backups`: optional; the maximum number of local backups to keep
	- as new local backups are created, old backups are purged to keep within
		the limit
	- this option only applies if you use date format sequences in
		`paths.local_backup` (the only case in which multiple backups for the
			same site would exist)
	- if option is omitted, all local backups are kept

Please see the included [example.ini](src/config/example.ini) file for an
example configuration.

### Adding a command alias

To make the utility easily accessible from the command line, you will need to
symlink the utility's driver script to `/usr/local/bin`. Doing so will allow you
to run the utility via the `ssh-wp-backup` command.

Assuming the CWD is the local project directory:

```
ln -sf "$PWD"/src/local.py /usr/local/bin/ssh-wp-backup
```

### Running the utility

#### Backing up

Once you have crafted one or more configuration files to your liking, you can
run the utility by invoking the command `ssh-wp-backup` and providing the path
to a configuration file. The utility will then back up the WordPress database
according to the parameters set in the configuration file.

```
ssh-wp-backup ../mysite-config.ini
```

The utility will display the download progress when copying the file from the
remote server to your local machine.

#### Restoring from backup

To restore a WordPress database to a local backup, specify the `--restore` or
`-r` option, along with the path to a compressed local backup.

```
ssh-wp-backup ../mysite-config.ini -r ../mysite-backup.sql.gz
```

#### Bypassing confirmation prompt

By default, the utility prompts you for confirmation before restoring from
backup. However, you may bypass this prompt by providing the `--force` or `-f`
option.

```
ssh-wp-backup ../mysite-config.ini -rf ../mysite-backup.sql.gz
```

#### Silencing output

To silence output from the utility (both *stdout* and *stderr*), use the
`--quiet` or `-q` option:

```
ssh-wp-backup -q ../mysite-config.ini
```

## Support

If you'd like to submit a bug report or feature request, please [submit an
issue on GitHub](https://github.com/caleb531/ssh-wp-backup/issues).
