#!/bin/sh
# MAKU container entrypoint.
# For the web server (CMD "streamlit ..."): write the domain-specific Streamlit
# settings, wait for the database and create/migrate the schema, then start.
# Any other command (e.g. "python manage_users.py hash") runs directly.
set -eu
if [ "${1:-}" = "streamlit" ]; then
  python /app/configure_streamlit.py
  python /app/scripts/init_db.py
fi
exec "$@"
