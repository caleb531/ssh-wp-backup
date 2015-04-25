#!/bin/bash
# Script to execute on local machine

# Parse the given iniuration file
ini_path="$1"
program_dir="$(python -c "import os.path; print(os.path.realpath('src'))")"
source "$program_dir"/deps/read_ini.sh
read_ini "$ini_path" --prefix ini

# Evaluate date format sequences in backup paths
ini__paths__remote_backup="$(date +"$ini__paths__remote_backup")"
# Expand ~ in local backup path
ini__paths__local_backup="${ini__paths__local_backup/#~/$HOME}"
# Ensure that intermediate directories in local backup path exist
mkdir -p "$(dirname "$ini__paths__local_backup")"

# Compressor defaults to gzip if no alternate compressor is provided
if [ -z "$ini__backup__compressor" ]; then
	ini__backup__compressor='gzip -c'
fi

# Connect to server via SSH and backup database
ssh -p "$ini__ssh__port" \
	"$ini__ssh__user@$ini__ssh__hostname" \
	bash -s < "$program_dir"/remote.sh \
		"$ini__paths__wordpress" \
		"$ini__paths__remote_backup" \
		"$ini__backup__compressor"

# Download exported database file
scp -P "$ini__ssh__port" \
	"$ini__ssh__user@$ini__ssh__hostname":"$ini__paths__remote_backup" \
	"$(date +"$ini__paths__local_backup")"

# Purge remote copy of backup if desired
if [ "$ini__backup__purge_remote" == 1 ]; then
	ssh -p "$ini__ssh__port" \
		"$ini__ssh__user@$ini__ssh__hostname" \
		rm -f "$ini__paths__remote_backup"
fi

# Prevent number of local backups from exceeding the maximum (if set)
if [ ! -z "$ini__backup__max_local_backups" ]; then
	python "$program_dir"/purge_oldest.py \
		"$program_dir" \
		"$ini__paths__local_backup" \
		"$ini__backup__max_local_backups"
fi
