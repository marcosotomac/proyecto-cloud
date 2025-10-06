#!/usr/bin/env python3
"""
Simple test to verify database configuration without requiring DB connection.
Tests imports, models, and configuration.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪 PostgreSQL Configuration Validation (Without DB Connection)")
print("=" * 70)
print()

# Test 1: Check if dependencies are installed
print("1️⃣  Checking dependencies...")
try:
    import sqlalchemy
    print(f"   ✅ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print(f"   ❌ SQLAlchemy not installed - run: pip install sqlalchemy")
    sys.exit(1)

try:
    import psycopg2
    print(f"   ✅ psycopg2: {psycopg2.__version__}")
except ImportError:
    print(f"   ❌ psycopg2 not installed - run: pip install psycopg2-binary")
    sys.exit(1)

print()

# Test 2: Check configuration
print("2️⃣  Checking configuration...")
try:
    from config import settings
    print(f"   ✅ Config loaded")
    print(f"   📊 Environment: {settings.environment}")
    print(f"   🗄️  Database URL: {settings.DATABASE_URL}")
    print(f"   📦 S3 Bucket: {settings.s3_bucket}")
except Exception as e:
    print(f"   ❌ Failed to load config: {e}")
    sys.exit(1)

print()

# Test 3: Check database module
print("3️⃣  Checking database module...")
try:
    from db import Base, engine, SessionLocal, get_db, init_db
    print(f"   ✅ Database module loaded")
    print(f"   ✅ Base class available")
    print(f"   ✅ Engine created")
    print(f"   ✅ SessionLocal configured")
    print(f"   ✅ get_db() dependency available")
    print(f"   ✅ init_db() function available")
except Exception as e:
    print(f"   ❌ Failed to load database module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Check models
print("4️⃣  Checking database models...")
try:
    from models.db_models import TTSConversion
    print(f"   ✅ TTSConversion model loaded")
    print(f"   📋 Table name: {TTSConversion.__tablename__}")

    # List all columns
    print(f"   📊 Columns:")
    for column in TTSConversion.__table__.columns:
        col_type = str(column.type)
        nullable = "NULL" if column.nullable else "NOT NULL"
        print(f"      • {column.name}: {col_type} ({nullable})")

    # Check for primary key
    pk_cols = [col.name for col in TTSConversion.__table__.primary_key]
    print(f"   🔑 Primary key: {', '.join(pk_cols)}")

    # Check for indexes
    if hasattr(TTSConversion.__table__, 'indexes'):
        print(f"   📇 Indexes: {len(TTSConversion.__table__.indexes)}")

    # Test model methods
    print(
        f"   ✅ to_dict() method available: {hasattr(TTSConversion, 'to_dict')}")

except Exception as e:
    print(f"   ❌ Failed to load models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Check if routes use the database
print("5️⃣  Checking routes integration...")
try:
    from routes.tts import router
    print(f"   ✅ TTS router loaded")

    # Check if get_db is imported
    import inspect
    source = inspect.getsource(inspect.getmodule(router))

    if 'from db import get_db' in source or 'from db import' in source:
        print(f"   ✅ Routes import database dependencies")
    else:
        print(f"   ⚠️  Routes might not be using database")

    if 'TTSConversion' in source:
        print(f"   ✅ Routes use TTSConversion model")
    else:
        print(f"   ⚠️  Routes might not be using TTSConversion model")

    if 'db.add' in source or 'db.commit' in source:
        print(f"   ✅ Routes perform database operations")
    else:
        print(f"   ⚠️  Routes might not be saving to database")

except Exception as e:
    print(f"   ⚠️  Could not verify routes: {e}")

print()

# Test 6: Verify environment files
print("6️⃣  Checking environment files...")
env_files = ['.env.dev', '.env.example']
for env_file in env_files:
    env_path = os.path.join(os.path.dirname(__file__), env_file)
    if os.path.exists(env_path):
        print(f"   ✅ {env_file} exists")
        with open(env_path, 'r') as f:
            content = f.read()
            if 'DATABASE_URL' in content:
                print(f"      ✅ Contains DATABASE_URL")
            else:
                print(f"      ⚠️  Missing DATABASE_URL")
    else:
        print(f"   ⚠️  {env_file} not found")

print()

# Summary
print("=" * 70)
print("✅ Configuration validation completed successfully!")
print("=" * 70)
print()
print("📝 Next steps:")
print("   1. Start PostgreSQL: docker-compose up -d postgres-tts")
print("   2. Run full test: python test_db_connection.py (with DB running)")
print("   3. Start service: docker-compose up --build text-speech-service")
print()
print("🔗 To test the database connection, ensure PostgreSQL is running:")
print("   docker-compose up -d postgres-tts")
print()
