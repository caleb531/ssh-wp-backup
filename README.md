# SSH WordPress Backup

*Copyright 2015 Caleb Evans*
*Released under the MIT license*

WordPress SSH Backup is a command line utility for creating local backups of a
remote WordPress database via SSH.

# Getting Started

## Requirements

This utility assumes that you have (or have access to) the following:

1. A Linux-based server with support for SSH
2. A remote WordPress installation on said server

## Configuring SSH

If you have not yet configured SSH key-based authentication on your server,
please follow the steps below. If you know what you're doing, feel free to skip
any of these instructions.

### Create an SSH key

To create a public SSH key for connecting to the remote server, run the
following command:

```
ssh-keygen
```

When prompted to enter a file in which to save the key, press *Enter*
immediately to save to the default location (`~/.ssh/id_rsa`). When prompted to
enter a passphrase, press `Enter` to leave the passphrase blank (this will
ensure that the utility works completely automatically).

### Copy the public key to the remote server

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

If all goes well, the shell will display a message indicating that a key has
been added. At this point, you can run the WordPress SSH Backup utility without
needing to authenticate again at any point.

## Configuration files

This command line utility requires a single argument: the path to a
specially-formatted configuration file. This configuration file *must* have the
`.ini` extension and *must* contain the following properties:

- `wordpress`: The absolute path to the remote WordPress site.
	- (*e.g.* `~/public_html/mysite`)
- `remote_backup`: The absolute path to the database backup file to be created.
	- For security, this path should be outside of the `public_html/` directory
	- The filename may include `date` format sequences such as `%Y`
	- (*e.g.* `~/mysitedb-%Y-%m-%d.sql.gz`)
- `local_backup`: The absolute path to the local backup file to be created
(or the path to its containing directory)
	- The filename may also include `date` format sequences
	- (*e.g.* `~/Documents/Backups/mysitedb-%Y-%m-%d.sql.gz`)
	- (*e.g.* `~/Documents/Backups`)

Please see the included `example.ini` file for an example configuration.

## Running the utility

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
