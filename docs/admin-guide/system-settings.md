# System Settings

The Settings page lets administrators configure system-wide preferences.

## General Settings

- **System Name** — The name displayed in the navigation bar and page titles
- **Timezone** — The default timezone for the system (affects timestamps and reports)

## Security Settings

- **Session Timeout** — How many minutes of inactivity before a user is automatically logged out
- **Password Policy** — Minimum password requirements (length, complexity)
- **Password Expiry** — Number of days before users must change their password

## Backup

- **Manual Backup** — Click "Run Backup" to create an immediate database backup
- **Backup Frequency** — Configure automatic backup scheduling

## Data Integrity

The "Check Data Integrity" tool scans the database for inconsistencies and reports any issues found. This is useful after migrations or data imports.

## Audit Logs

All administrative actions are recorded in the audit log. The log captures:

- Who performed the action
- What action was taken
- When it happened
- The IP address and user agent

Audit logs are visible to administrators in the Settings page.
