#!/bin/sh
# Nightly logical backup of the MAKU database with N-day retention.
# Restore:  gunzip -c backups/maku-YYYYmmdd-HHMM.sql.gz | docker compose exec -T db psql -U maku -d maku
set -eu
mkdir -p /backups
echo "[backup] scheduler started - daily at ${BACKUP_HOUR_UTC}:00 UTC, keep ${BACKUP_RETENTION_DAYS} days"
while true; do
  now_h=$(date -u +%H | sed 's/^0//'); now_h=${now_h:-0}
  if [ "$now_h" -eq "${BACKUP_HOUR_UTC}" ]; then
    file="/backups/maku-$(date -u +%Y%m%d-%H%M).sql.gz"
    if pg_dump --no-owner --no-privileges | gzip -9 > "$file.tmp"; then
      mv "$file.tmp" "$file"; echo "[backup] wrote $file"
    else
      rm -f "$file.tmp"; echo "[backup] FAILED" >&2
    fi
    find /backups -name 'maku-*.sql.gz' -mtime +"${BACKUP_RETENTION_DAYS}" -delete
    sleep 3700   # step past the current hour
  fi
  sleep 300
done
