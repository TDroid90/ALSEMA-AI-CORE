# Backup and restore

The Core database is stored in the `postgres_data` Docker volume. The approved
backup procedure exports a portable SQL dump rather than copying live database
files.

From the repository root, create a backup:

```powershell
.\scripts\backup.ps1 -Destination .\backups
```

To restore a dump into the running local stack:

```powershell
.\scripts\restore.ps1 -BackupFile .\backups\alsema-YYYYMMDD-HHMMSS.sql
```

Restore replaces database objects represented by the dump. Stop user activity
before restoring and take a fresh backup first. Redis is an operational queue and
is not restored; pending jobs should be re-created from durable application state.
