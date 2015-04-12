#!/bin/bash
# Script to execute on remote server via SSH

# Assign more-meaningful names to received script parameters
wp_dir="$1"
backup_path="$2"

# Retrieve and store contents of wp-config
wp_config_path="$wp_dir/wp-config.php"
wp_config="$(< $wp_config_path)"

# Retrieve value for the given key in wp-config
get_config_value() {
	local key_name="$1"
	echo "$wp_config" | grep -oP "(?<=define\('$key_name', ')(.*)(?='\);)"
}

# Database information
db_host="$(get_config_value DB_HOST)"
db_name="$(get_config_value DB_NAME)"
db_user="$(get_config_value DB_USER)"
db_pswd="$(get_config_value DB_PASSWORD)"

# Export MySQL database to compressed file
mysqldump "$db_name" \
	--add-drop-table \
	-h "$db_host" \
	-u "$db_user" \
	-p"$db_pswd" \
	| gzip -c > "$backup_path"
