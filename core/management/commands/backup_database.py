import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Create a backup of the database and uploaded files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='Directory to store backups (default: backups)',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup file',
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='Include media files in backup',
        )

    def handle(self, *args, **options):
        backup_dir = Path(options['backup_dir'])
        compress = options['compress']
        include_media = options['include_media']
        
        # Create backup directory if it doesn't exist
        backup_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'dmp_backup_{timestamp}'
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            self.stdout.write(self.style.SUCCESS(f'Creating backup: {backup_name}'))
            
            # Backup database
            self._backup_database(backup_path)
            
            # Backup media files if requested
            if include_media:
                self._backup_media(backup_path)
            
            # Create backup info file
            self._create_backup_info(backup_path)
            
            # Compress if requested
            if compress:
                self._compress_backup(backup_dir, backup_name)
                # Remove uncompressed directory
                shutil.rmtree(backup_path)
                backup_path = backup_dir / f'{backup_name}.tar.gz'
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Backup completed successfully: {backup_path}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )
            # Clean up on failure
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            raise CommandError(f'Backup failed: {str(e)}')

    def _backup_database(self, backup_path):
        """Backup the database"""
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            # SQLite backup
            db_path = Path(db_config['NAME'])
            if db_path.exists():
                backup_db_path = backup_path / 'database.sqlite3'
                shutil.copy2(db_path, backup_db_path)
                self.stdout.write('Database backed up (SQLite)')
            else:
                raise CommandError(f'Database file not found: {db_path}')
                
        elif db_config['ENGINE'] == 'django.db.backends.postgresql':
            # PostgreSQL backup using pg_dump
            backup_db_path = backup_path / 'database.sql'
            cmd = [
                'pg_dump',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-f', str(backup_db_path),
                '--verbose',
                '--no-password'
            ]
            
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise CommandError(f'pg_dump failed: {result.stderr}')
            
            self.stdout.write('Database backed up (PostgreSQL)')
            
        elif db_config['ENGINE'] == 'django.db.backends.mysql':
            # MySQL backup using mysqldump
            backup_db_path = backup_path / 'database.sql'
            cmd = [
                'mysqldump',
                '-h', db_config.get('HOST', 'localhost'),
                '-P', str(db_config.get('PORT', 3306)),
                '-u', db_config['USER'],
                f'-p{db_config["PASSWORD"]}',
                db_config['NAME']
            ]
            
            with open(backup_db_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise CommandError(f'mysqldump failed: {result.stderr}')
            
            self.stdout.write('Database backed up (MySQL)')
            
        else:
            # Generic Django backup using dumpdata
            backup_db_path = backup_path / 'database.json'
            with open(backup_db_path, 'w') as f:
                call_command('dumpdata', stdout=f, indent=2)
            
            self.stdout.write('Database backed up (Django dumpdata)')

    def _backup_media(self, backup_path):
        """Backup media files"""
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root and Path(media_root).exists():
            media_backup_path = backup_path / 'media'
            shutil.copytree(media_root, media_backup_path)
            self.stdout.write('Media files backed up')
        else:
            self.stdout.write('No media files to backup')

    def _create_backup_info(self, backup_path):
        """Create backup information file"""
        info_content = f"""DMP Database Backup Information
===============================

Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Django Version: {self._get_django_version()}
Database Engine: {settings.DATABASES['default']['ENGINE']}
Database Name: {settings.DATABASES['default']['NAME']}
Python Version: {self._get_python_version()}

Backup Contents:
- Database: Yes
- Media Files: {'Yes' if (backup_path / 'media').exists() else 'No'}

Restore Instructions:
1. For SQLite: Replace your database.sqlite3 with the backed up file
2. For PostgreSQL/MySQL: Use appropriate restore commands (psql/mysql)
3. For Django JSON: Use 'python manage.py loaddata database.json'
4. Copy media files back to MEDIA_ROOT if included

Notes:
- Ensure the same Django version when restoring
- Run migrations after restoring if needed
- Update file permissions as necessary
"""
        
        info_path = backup_path / 'backup_info.txt'
        info_path.write_text(info_content)

    def _compress_backup(self, backup_dir, backup_name):
        """Compress the backup directory"""
        backup_path = backup_dir / backup_name
        archive_path = backup_dir / f'{backup_name}.tar.gz'
        
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'gztar',
            str(backup_path)
        )
        
        self.stdout.write(f'Backup compressed: {archive_path}')

    def _get_django_version(self):
        """Get Django version"""
        import django
        return django.get_version()

    def _get_python_version(self):
        """Get Python version"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"