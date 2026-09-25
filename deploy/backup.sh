#!/bin/sh
set -eu
umask 077

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="/backups/$stamp"
mkdir -p "$destination"

pg_dump --format=custom --file="$destination/postgres.dump"
tar -C /data -czf "$destination/files.tar.gz" media reports
printf 'PostgreSQL, mídia e relatórios concluídos em %s\n' "$destination" > "$destination/COMPLETE"
printf 'Backup concluído: %s\n' "$destination"
