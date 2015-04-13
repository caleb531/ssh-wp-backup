#!/bin/bash
# Script to execute on local machine

# Parse the given iniuration file
ini_path="$1"
program_dir="$(dirname "$(readlink -f "$0")")"
source "$program_dir"/deps/read_ini.sh
read_ini "$ini_path" --prefix ini

# Expands ~ to full home directory path
expand_home() {
	echo "${1/#~/$HOME}"
}
# Evaluate date format sequences in backup paths
ini__paths__remote_backup="$(date +"$ini__paths__remote_backup")"
ini__paths__local_backup="$(date +"$ini__paths__local_backup")"
# Expand ~ in local backup path
ini__paths__local_backup="$(expand_home "$ini__paths__local_backup")"

# Compressor defaults to gzip if no alternate compressor is provided
if [ -z "$ini__db__compressor" ]; then
	ini__db__compressor='gzip -c'
fi

# Connect to server via SSH and backup database
ssh -p "$ini__ssh__port" \
	"$ini__ssh__user@$ini__ssh__hostname" \
	'bash -s' < "$program_dir"/remote.sh \
		"$ini__paths__wordpress" \
		"$ini__paths__remote_backup" \
		"$ini__db__compressor"

# Download exported database file
scp -P "$ini__ssh__port" \
	"$ini__ssh__user@$ini__ssh__hostname":"$ini__paths__remote_backup" \
	"$ini__paths__local_backup"
