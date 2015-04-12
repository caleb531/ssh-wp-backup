#!/bin/bash
# Script to execute on local machine

# Parse the given configuration file
config_path="$1"
program_dir="$(dirname "${BASH_SOURCE[0]}")"
source "$program_dir"/deps/read_ini.sh
read_ini "$config_path" --prefix config

# Expands ~ to full home directory path
expand_home() {
	echo "${1/#~/$HOME}"
}
config__paths__remote_backup="$(date +"$config__paths__remote_backup")"
config__paths__local_backup="$(date +"$config__paths__local_backup")"
config__paths__local_backup="$(expand_home "$config__paths__local_backup")"

# Connect to server via SSH and backup database
ssh -p "$config__ssh__port" \
	"$config__ssh__user" \
	'bash -s' < "$program_dir"/remote.sh \
		"$config__paths__wordpress" \
		"$config__paths__remote_backup"

# Download exported database file
scp -P "$config__ssh__port" \
	"$config__ssh__user":"$config__paths__remote_backup" \
	"$config__paths__local_backup"
