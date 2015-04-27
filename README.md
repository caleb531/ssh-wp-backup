# SSH WordPress Backup (beta)

*Copyright 2015 Caleb Evans*  
*Released under the MIT license*

SSH WordPress Backup is a command line utility for creating local backups of a
remote WordPress database via SSH.

Please note that this utility is under active development, and therefore is
subject to frequent and sudden API changes. Use at your own risk.

## Getting Started

### Requirements

This utility assumes that you have (or have access to) the following:

- A Linux server with support for SSH
- SSH access to said server
- A WordPress installation on said server
- The `mysqldump` utility installed on said server

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

- `wordpress`: the absolute path to the remote WordPress site
	- *e.g.* `~/public_html/mysite`
- `remote_backup`: the absolute path to the database backup file to be created
	- for security, this path should be outside of the `public_html/` directory
	- the filename may include [date format sequences](http://strftime.org/)
		such as `%Y`
	- the utility will automatically create intermediate directories apart of
		the path if they do not exist
	- *e.g.* `~/backups/mysitedb-%Y-%m-%d.sql.gz`
- `local_backup`: the absolute path to the local backup file to be created (or
	the path to its containing directory)
	- the filename may also include `date` format sequences
	- like `remote_backup`, the utility will also create intermediate
		directories
	- *e.g.* `~/Documents/Backups/%Y-%m-%d/mysitedb-%H-%M-%S.sql.gz`
	- *e.g.* `~/Documents/Backups`

#### [ssh]

- `user`: the name of the user under which to log in
	- This is concatenated with the given hostname internally
	- *e.g.* `myname`
- `hostname`: the hostname or IP address used to connect.
- `port`: the port number used to connect

#### [backup]

- `compressor`: optional; an alternate compressor to use for compressing the
	database backup on the server (may include command line arguments)
	- defaults to `gzip` if no compressor is given
	- if you specify this option, you must ensure that the file extensions for
		`paths.remote_backup` and `paths.local_backup` match that of the chosen
		compressor
	- *e.g.* `bzip2`
- `purge_remote`: optional; a boolean indicating if the remote copy of the
	backup should be purged after download
	- valid values include `yes`, `no`, `on`, `off`, `true`, `false`, `1`, and
		`0`
	- default value is `no`
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

Once you have crafted one or more configuration files to your liking, you can
run the utility by invoking the command `ssh-wp-backup` and providing the path
to a configuration file.

Again, assuming the CWD is the local project directory, *and* assuming that your
chosen configuration file is stored alongside the project directory:

```
./ssh-wp-backup/src/local.py ../mysite-config.ini
```

The utility will display the download progress when copying the file from the
remote server to your local machine.

## Support

If you'd like to submit a bug report or feature request, please [submit an
issue on GitHub](https://github.com/caleb531/ssh-wp-backup/issues).
