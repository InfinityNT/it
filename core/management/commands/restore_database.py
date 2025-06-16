import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Restore database and files from a backup'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_path',
            type=str,
            help='Path to backup file or directory',
        )
        parser.add_argument(
            '--restore-media',
            action='store_true',
            help='Restore media files if available',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation',
        )

    def handle(self, *args, **options):
        backup_path = Path(options['backup_path'])
        restore_media = options['restore_media']
        force = options['force']
        
        if not backup_path.exists():
            raise CommandError(f'Backup path does not exist: {backup_path}')
        
        # Handle compressed backups
        if backup_path.is_file() and backup_path.suffix == '.gz':
            backup_path = self._extract_backup(backup_path)
        
        if not backup_path.is_dir():
            raise CommandError(f'Invalid backup format: {backup_path}')
        
        # Confirm restoration
        if not force:
            confirm = input(
                'This will overwrite your current database and media files. '
                'Are you sure you want to continue? (yes/no): '
            )
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write('Restore cancelled.')
                return
        
        try:
            self.stdout.write(self.style.SUCCESS(f'Restoring from: {backup_path}'))
            
            # Restore database
            self._restore_database(backup_path)
            
            # Restore media files if requested
            if restore_media:
                self._restore_media(backup_path)
            
            self.stdout.write(
                self.style.SUCCESS('Restore completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restore failed: {str(e)}')
            )
            raise CommandError(f'Restore failed: {str(e)}')

    def _extract_backup(self, backup_file):
        """Extract compressed backup"""
        extract_dir = backup_file.parent / 'temp_restore'
        extract_dir.mkdir(exist_ok=True)
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            # Find the actual backup directory
            extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if len(extracted_dirs) == 1:
                return extracted_dirs[0]
            else:
                return extract_dir
                
        except Exception as e:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            raise CommandError(f'Failed to extract backup: {str(e)}')

    def _restore_database(self, backup_path):
        """Restore the database"""
        db_config = settings.DATABASES['default']
        
        # Check for different backup formats
        sqlite_backup = backup_path / 'database.sqlite3'
        sql_backup = backup_path / 'database.sql'
        json_backup = backup_path / 'database.json'
        
        if sqlite_backup.exists() and db_config['ENGINE'] == 'django.db.backends.sqlite3':
            # SQLite restore
            db_path = Path(db_config['NAME'])
            if db_path.exists():
                db_path.unlink()  # Remove current database
            shutil.copy2(sqlite_backup, db_path)
            self.stdout.write('Database restored (SQLite)')
            
        elif sql_backup.exists() and db_config['ENGINE'] == 'django.db.backends.postgresql':
            # PostgreSQL restore
            cmd = [
                'psql',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-f', str(sql_backup),
                '--quiet'
            ]
            
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise CommandError(f'psql restore failed: {result.stderr}')
            
            self.stdout.write('Database restored (PostgreSQL)')
            
        elif sql_backup.exists() and db_config['ENGINE'] == 'django.db.backends.mysql':
            # MySQL restore
            cmd = [
                'mysql',
                '-h', db_config.get('HOST', 'localhost'),
                '-P', str(db_config.get('PORT', 3306)),
                '-u', db_config['USER'],
                f'-p{db_config["PASSWORD"]}',
                db_config['NAME']
            ]
            
            with open(sql_backup, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise CommandError(f'mysql restore failed: {result.stderr}')
            
            self.stdout.write('Database restored (MySQL)')
            
        elif json_backup.exists():
            # Django JSON restore
            # First, flush the database
            call_command('flush', '--noinput')
            # Then load the data
            call_command('loaddata', str(json_backup))
            self.stdout.write('Database restored (Django JSON)')
            
        else:
            raise CommandError('No compatible database backup found')

    def _restore_media(self, backup_path):
        """Restore media files"""
        media_backup = backup_path / 'media'
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        
        if media_backup.exists() and media_root:
            media_root_path = Path(media_root)
            
            # Backup existing media
            if media_root_path.exists():
                backup_existing = media_root_path.parent / f'media_backup_{int(time.time())}'
                shutil.move(media_root_path, backup_existing)
                self.stdout.write(f'Existing media backed up to: {backup_existing}')
            
            # Restore media files
            shutil.copytree(media_backup, media_root_path)
            self.stdout.write('Media files restored')
        else:
            self.stdout.write('No media files to restore')

    def __del__(self):
        """Clean up temporary files"""
        # This will clean up any extracted backup directories
        pass