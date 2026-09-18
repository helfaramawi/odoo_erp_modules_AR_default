# Ops scripts — Windows batch files for the Docker Compose stack

Everyday start/stop/backup/restore for `demo_edition`'s Docker Compose
stack. Double-click from Explorer, or run from `cmd`/PowerShell — each
script `cd`s to `demo_edition` itself, so it works from any location.

| Script | What it does |
|---|---|
| `start.bat` | Rebuilds the Odoo image and brings the stack up (`docker compose up -d --build`). |
| `restart.bat` | Same as `start.bat`. Exists as a separate, clearly-named script because a plain `docker compose restart` does **not** pick up code changes — see below. |
| `stop.bat` | Stops the containers. Data (database + filestore) is untouched. |
| `backup.bat` | Full backup into `backups\<timestamp>\`: `database.dump` (pg_dump), `filestore.tar.gz` (Odoo attachments), `config_and_addons.zip` (`.env` + `docker\` + `addons\`). |
| `restore.bat [timestamp]` | Restores the database and filestore from a `backup.bat` snapshot. **Destructive** — asks for a typed `YES` confirmation first. The config/addons zip is only extracted alongside for manual review, never applied automatically over your live code. |

## Why `--build` every time

This project's `docker/Dockerfile` `COPY`s the `addons/` folder into the
image at *build* time — it is not a live bind-mount. That means
`docker compose restart` (or starting without `--build`) keeps serving
whatever code was baked in at the last build, even after a `git pull`.
`start.bat`/`restart.bat` always pass `--build` so the running container
matches what is actually on disk.

An image rebuild refreshes the **code**. It does not touch the
**database** — after a restart, if a module's views, security rules, or
data files changed, you still need a separate Apps → Upgrade for that
module from inside Odoo.

## Backups directory

`backups/` is git-ignored (see the repo root `.gitignore`) — dumps and
filestore archives can contain real demo data and have no business in
version control. Back up to (and restore from) an external drive or
cloud storage separately if you need off-machine copies.
