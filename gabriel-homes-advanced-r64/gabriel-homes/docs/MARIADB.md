# Running Gabriel Homes on MariaDB

The project uses MariaDB 10.11 or later in production. Django's `mysql` backend
drives MariaDB; the connection string below is a `mysql://` URL.

## 1. Create the database and user

```sql
CREATE DATABASE gabriel_homes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gabriel'@'localhost' IDENTIFIED BY 'a-long-random-password';
GRANT ALL ON gabriel_homes.* TO 'gabriel'@'localhost';
-- The restore drill loads backups into a scratch database named <db>_restore_drill:
GRANT ALL ON `gabriel\_homes\_restore\_drill`.* TO 'gabriel'@'localhost';
FLUSH PRIVILEGES;
```

Always use `utf8mb4`. The project relies on it for every character the owner might type.

## 2. Install the driver

The project uses `mysqlclient`, which builds against the MariaDB client library.

```bash
# Debian / Ubuntu
sudo apt install -y mariadb-server libmariadb-dev pkg-config build-essential
pip install -r requirements.txt
```

On Windows, install the MariaDB Connector/C and then `pip install mysqlclient`, or
ask for a prebuilt wheel. If that is not practical on the owner's machine, the
development copy can run on SQLite; production runs on MariaDB.

## 3. Point the project at it

Put the URL in `.env`. If the password contains characters such as `@`, `:`, `/` or `#`,
percent-encode them (for example `@` becomes `%40`).

```
DATABASE_URL=mysql://gabriel:a-long-random-password@localhost:3306/gabriel_homes
```

The production settings refuse to start without a `mysql://` (or `postgres://`) URL.
They never fall back to SQLite.

## 4. Build the schema and create the owner

```bash
python manage.py migrate
python manage.py bootstrap_owner --password '<temporary>'
python manage.py check --deploy
```

Migration `0007_portable_cover_constraint` is the one that makes "one cover photo per
listing" work on MariaDB. MariaDB cannot enforce that rule with a conditional index, so the
rule is now a unique constraint on `(property, cover_slot)`.

## 5. Run the test suite against MariaDB

The suite must pass on both databases. The MariaDB run uses a dedicated settings module and
creates its own `test_<name>` database:

```bash
GABRIEL_TEST_DB_URL=mysql://gabriel:password@localhost:3306/gabriel \
DJANGO_SETTINGS_MODULE=config.settings.test_mariadb \
python -m pytest apps -q
```

The database named in the URL must exist; pytest-django creates and drops `test_<name>`.

## 6. Backups and restore

```bash
DATABASE_URL=mysql://gabriel:...@localhost:3306/gabriel_homes ./scripts/backup-db.sh
DATABASE_URL=mysql://gabriel:...@localhost:3306/gabriel_homes ./scripts/restore-drill.sh
```

The backup uses `mariadb-dump --single-transaction`, so it does not lock the site while it runs.
The password is passed through a temporary option file, not on the command line.
Backups older than 30 days are removed; use `--keep-days` to change that.
Run the restore drill at least monthly. It restores the newest backup into a scratch database,
checks that tables came back, and removes the scratch database. It never touches the live one.

## 7. Things that differ from PostgreSQL

- **Case-insensitive comparisons.** The `utf8mb4_unicode_ci` collation compares strings
  without regard to case. Account emails are stored in lower case and login matches them
  case-insensitively, so behaviour is the same on both databases. Slugs are lower case by
  construction.
- **Strict mode.** The connection runs in `STRICT_TRANS_TABLES`, so over-long values are rejected
  rather than silently truncated.
- **Search.** Free-text search uses case-insensitive `LIKE` matching on MariaDB and SQLite. The
  PostgreSQL full-text path is not used.
- **Conditional unique indexes** are not available. The cover-photo rule is enforced with
  `cover_slot` instead (see step 4).
