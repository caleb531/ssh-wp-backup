# SSH WordPress Backup (beta)

*Copyright 2015 Caleb Evans*  
*Released under the MIT license*

SSH WordPress Backup is a command line utility for creating local backups of a
remote WordPress database via SSH.

Please note that this utility is under active development, and therefore is
subject to frequent and sudden API changes.

## Getting Started

### Requirements

This utility assumes that you have (or have access to) the following:

- A Linux-based server with support for SSH
- SSH access to said server
- A remote WordPress installation on said server
- The `readlink` command installed locally (can be installed via `coreutils`
	package if missing)
	- OS X (via Homebrew): `brew install coreutils`
	- Linux: `apt-get install coreutils`

### Configuring SSH

If you have not yet configured SSH key-based authentication on your server,
please follow the steps below. If you know what you're doing, feel free to skip
any of these instructions.

#### 1. Create an SSH key

To create a public SSH key for connecting to the remote server, run the
following command:

```
ssh-keygen
```

When prompted to enter a file in which to save the key, press *Enter*
immediately to save to the default location (`~/.ssh/id_rsa`). When prompted to
enter a passphrase, press `Enter` to leave the passphrase blank (this will
ensure that the utility works completely automatically).

#### 2. Copy the public key to the remote server

To copy your newly-created public SSH key to the remote server, run the
following command. You will need to specify the server user in the form
`user@hostname`.

In addition, you will likely need to specify the port number via the `-p` flag.
The port is typically `2222` for SSH connections, though you should check with
the server's administrator or hosting provider to confirm this.

```
ssh-copy-id -p 2222 yourname@yoursite.com
```

You may be notified that the authenticity of the host can't be established. When
asked if you want to continue connecting, type `yes` and press *Enter*.

When prompted, enter the password for the given user. This is often the password
for your hosting account's control panel, assuming you are the only user.

#### 3. You're done!

If all goes well, the shell will display a message indicating that a key has
been added. At this point, you can run the WordPress SSH Backup utility without
needing to authenticate again at any point.

### Configuration files

This command line utility requires a single argument: the path to a
specially-formatted configuration file. This configuration file *must* have the
`.ini` extension and *must* contain the following properties:

#### [paths]

- `wordpress`: the absolute path to the remote WordPress site
	- *e.g.* `~/public_html/mysite`
- `remote_backup`: the absolute path to the database backup file to be created
	- for security, this path should be outside of the `public_html/` directory
	- the filename may include `date` format sequences such as `%Y`
	- *e.g.* `~/mysitedb-%Y-%m-%d.sql.gz`
- `local_backup`: the absolute path to the local backup file to be created (or
	the path to its containing directory)
	- the filename may also include `date` format sequences
	- *e.g.* `~/Documents/Backups/mysitedb-%Y-%m-%d.sql.gz`
	- *e.g.* `~/Documents/Backups`

#### [ssh]

- `user`: the name of the user under which to log in
	- This is concatenated with the given hostname internally
	- *e.g.* `myname`
- `hostname`: the hostname or IP address used to connect.
- `port`: the port number used to connect

#### [backup]

- `compressor`: optional; an alternate compressor to use (including command line
	arguments)
	- compressor *must* send output to stdout
	- defaults to `gzip -c` if not compressor is given
	- if you specify this option, you must ensure that the file extensions for
		`paths.remote_backup` and `paths.local_backup` match that of the chosen
		compressor
	- *e.g.* `bzip2 -c`
- `purge_remote`: optional; a boolean indicating if the remote copy of the
	backup should be purged after download
	- valid values include `true`, `false`, `yes`, `no`, `on`, and `off`
	- default value is `no`

Please see the included [example.ini](example.ini) file for an example
configuration.

### Running the utility

Once you have crafted one or more configuration files to your liking, you can
run the utility by executing the script `src/local.sh` and providing the path to
a configuration file.

Assuming the CWD is the containing directory of the cloned project, and assuming
that your preferred configuration file is stored in a directory `myconfigs/`:

```
./ssh-wp-backup/src/local.sh ./myconfigs/mysite-config.ini
```

The utility will display the download progress (provided by `scp`) when copying
the file from the remote server to your local machine.

### Adding a command alias (optional)

For convenience, you may wish to symlink this utility into `/usr/local/bin` so
you do not need to type the full path every time you wish to run it.

Again, assuming the CWD is the containing directory of the cloned project:

```
ln -s "$PWD"/ssh-wp-backup/src/local.sh /usr/local/bin/ssh-wp-backup
```

## Support

If you'd like to submit a bug report or feature request, please [submit an
issue on GitHub](https://github.com/caleb531/ssh-wp-backup/issues).
