#!/bin/bash
# Script to execute on local machine

config_path="$1"
program_dir="$(dirname "${BASH_SOURCE[0]}")"
source "$program_dir"/deps/read_ini.sh
read_ini "$config_path" --prefix config

# Expand ~ to full home directory path for the given path
expand_home() {
	echo "${1/#~/$HOME}"
}
config__paths__local_backup="$(expand_home "$config__paths__local_backup")"

# If all necessary configuration variables have been provided
if [[ ! -z $config__paths__wordpress && ! -z $config__paths__remote_backup && ! -z $config__paths__local_backup && ! -z $config__ssh__user ]]; then

	# Connect to server via SSH and backup database
	ssh -p 2222 \
		"$config__ssh__user" \
		'bash -s' < "$program_dir"/remote.sh \
			"$config__paths__wordpress" \
			"$config__paths__remote_backup"

	# Download exported database file
	scp -P 2222 \
		"$config__ssh__user":"$config__paths__remote_backup" \
		"$config__paths__local_backup"

else

	echo SAD

fi
