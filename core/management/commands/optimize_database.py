from django.core.management.base import BaseCommand
from django.db import connection
import time


class Command(BaseCommand):
    help = 'Optimize SQLite database for better performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only run ANALYZE, skip VACUUM',
        )
        parser.add_argument(
            '--check-performance',
            action='store_true',
            help='Check query performance after optimization',
        )

    def handle(self, *args, **options):
        """Optimize SQLite database performance"""
        cursor = connection.cursor()
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting database optimization...')
        )
        
        # Get database size before optimization
        cursor.execute("PRAGMA page_count;")
        page_count_before = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size;")
        page_size = cursor.fetchone()[0]
        
        size_before_mb = (page_count_before * page_size) / (1024 * 1024)
        
        self.stdout.write(f"📊 Database size before: {size_before_mb:.2f} MB")
        
        if not options['analyze_only']:
            # VACUUM - Reclaim unused space and defragment
            self.stdout.write("🧹 Running VACUUM (reclaiming space)...")
            start_time = time.time()
            cursor.execute("VACUUM;")
            vacuum_time = time.time() - start_time
            self.stdout.write(f"   ✅ Completed in {vacuum_time:.2f} seconds")
        
        # ANALYZE - Update query planner statistics
        self.stdout.write("📈 Running ANALYZE (updating statistics)...")
        start_time = time.time()
        cursor.execute("ANALYZE;")
        analyze_time = time.time() - start_time
        self.stdout.write(f"   ✅ Completed in {analyze_time:.2f} seconds")
        
        # Get database size after optimization
        cursor.execute("PRAGMA page_count;")
        page_count_after = cursor.fetchone()[0]
        size_after_mb = (page_count_after * page_size) / (1024 * 1024)
        
        space_saved_mb = size_before_mb - size_after_mb
        
        self.stdout.write(f"📊 Database size after: {size_after_mb:.2f} MB")
        if space_saved_mb > 0:
            self.stdout.write(f"💾 Space reclaimed: {space_saved_mb:.2f} MB")
        
        # Show database statistics
        self.stdout.write("\n📋 Database Statistics:")
        
        # Table record counts
        from devices.models import Device, DeviceHistory
        from assignments.models import Assignment
        
        device_count = Device.objects.count()
        assignment_count = Assignment.objects.count()
        history_count = DeviceHistory.objects.count()
        
        self.stdout.write(f"   📱 Devices: {device_count:,}")
        self.stdout.write(f"   📋 Assignments: {assignment_count:,}")
        self.stdout.write(f"   📜 History records: {history_count:,}")
        
        # Check index usage
        cursor.execute("""
            SELECT name, tbl_name 
            FROM sqlite_master 
            WHERE type='index' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name;
        """)
        indexes = cursor.fetchall()
        
        self.stdout.write(f"   🗂️  Database indexes: {len(indexes)}")
        
        if options['check_performance']:
            self.stdout.write("\n⚡ Performance Check:")
            self._check_query_performance()
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Database optimization completed!')
        )
        self.stdout.write(
            self.style.WARNING(
                '💡 Tip: Run this command weekly for optimal performance'
            )
        )

    def _check_query_performance(self):
        """Check performance of common queries"""
        from devices.models import Device
        from assignments.models import Assignment
        
        # Test common queries
        test_queries = [
            ("Device list query", lambda: list(Device.objects.select_related('device_model', 'assigned_to')[:100])),
            ("Available devices", lambda: Device.objects.filter(status='available').count()),
            ("Active assignments", lambda: Assignment.objects.filter(status='active').count()),
            ("Device search", lambda: list(Device.objects.filter(asset_tag__icontains='LAP')[:10])),
        ]
        
        for query_name, query_func in test_queries:
            start_time = time.time()
            try:
                query_func()
                query_time = time.time() - start_time
                
                if query_time < 0.1:
                    status = self.style.SUCCESS(f"⚡ Fast")
                elif query_time < 0.5:
                    status = self.style.WARNING(f"⚠️  Acceptable")
                else:
                    status = self.style.ERROR(f"🐌 Slow")
                
                self.stdout.write(f"   {query_name}: {query_time:.3f}s {status}")
                
            except Exception as e:
                self.stdout.write(f"   {query_name}: ❌ Error - {e}")