#!/usr/bin/env python3
"""
Test script to verify PostgreSQL database configuration and connectivity.
This script can be run locally or inside the container to validate the setup.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported"""
    print("=" * 60)
    print("1️⃣  Testing imports...")
    print("=" * 60)

    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import SQLAlchemy: {e}")
        return False

    try:
        import psycopg2
        print(f"✅ psycopg2 version: {psycopg2.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import psycopg2: {e}")
        return False

    try:
        from config import settings
        print(f"✅ Config loaded successfully")
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    print()
    return True


def test_database_models():
    """Test that database models are defined correctly"""
    print("=" * 60)
    print("2️⃣  Testing database models...")
    print("=" * 60)

    try:
        from db import Base, engine
        from models.db_models import TTSConversion

        print(f"✅ Base class imported")
        print(f"✅ TTSConversion model imported")
        print(f"   Table name: {TTSConversion.__tablename__}")
        print(
            f"   Columns: {', '.join([col.name for col in TTSConversion.__table__.columns])}")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_database_connection():
    """Test connection to PostgreSQL database"""
    print("=" * 60)
    print("3️⃣  Testing database connection...")
    print("=" * 60)

    try:
        from sqlalchemy import create_engine, text
        from config import settings

        # Try to connect
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Successfully connected to PostgreSQL")
            print(f"   Version: {version}")

            # Test if we can create tables
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"   Database: {db_name}")

            result = conn.execute(text("SELECT current_user"))
            user = result.scalar()
            print(f"   User: {user}")

        print()
        return True

    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"   Make sure PostgreSQL is running and DATABASE_URL is correct")
        print()
        return False


def test_table_creation():
    """Test creating tables in the database"""
    print("=" * 60)
    print("4️⃣  Testing table creation...")
    print("=" * 60)

    try:
        from db import init_db, engine
        from sqlalchemy import inspect, text

        # Initialize database (create tables)
        init_db()

        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"✅ Tables created successfully")
        print(f"   Tables in database: {', '.join(tables)}")

        if 'tts_conversions' in tables:
            print(f"\n✅ tts_conversions table exists")

            # Get column details
            columns = inspector.get_columns('tts_conversions')
            print(f"   Columns:")
            for col in columns:
                print(f"      - {col['name']}: {col['type']}")

            # Get indexes
            indexes = inspector.get_indexes('tts_conversions')
            if indexes:
                print(f"\n   Indexes:")
                for idx in indexes:
                    print(f"      - {idx['name']}: {idx['column_names']}")
        else:
            print(f"❌ tts_conversions table not found")
            return False

        print()
        return True

    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_crud_operations():
    """Test basic CRUD operations"""
    print("=" * 60)
    print("5️⃣  Testing CRUD operations...")
    print("=" * 60)

    try:
        from db import SessionLocal
        from models.db_models import TTSConversion
        import uuid

        db = SessionLocal()

        # CREATE
        test_conversion = TTSConversion(
            user_id="test_user_123",
            text="Hello, this is a test",
            audio_url="s3://test-bucket/test.mp3",
            model="gtts",
            voice="en",
            language="en",
            file_size_bytes=12345,
            s3_key="test/test.mp3",
            s3_bucket="test-bucket",
            metadata={"test": True, "purpose": "validation"}
        )

        db.add(test_conversion)
        db.commit()
        db.refresh(test_conversion)

        print(f"✅ CREATE: Inserted test record with ID: {test_conversion.id}")

        # READ
        retrieved = db.query(TTSConversion).filter(
            TTSConversion.id == test_conversion.id
        ).first()

        if retrieved:
            print(f"✅ READ: Retrieved record successfully")
            print(f"   User ID: {retrieved.user_id}")
            print(f"   Text: {retrieved.text}")
            print(f"   Model: {retrieved.model}")

        # UPDATE
        retrieved.model = "gtts-updated"
        db.commit()
        print(f"✅ UPDATE: Updated model field")

        # COUNT
        count = db.query(TTSConversion).count()
        print(f"✅ COUNT: Total records in database: {count}")

        # DELETE (cleanup)
        db.delete(retrieved)
        db.commit()
        print(f"✅ DELETE: Cleaned up test record")

        db.close()
        print()
        return True

    except Exception as e:
        print(f"❌ Failed CRUD operations: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 PostgreSQL Database Configuration Test")
    print("=" * 60)
    print()

    results = []

    # Run tests in sequence
    results.append(("Imports", test_imports()))
    results.append(("Database Models", test_database_models()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("Table Creation", test_table_creation()))
    results.append(("CRUD Operations", test_crud_operations()))

    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("🎉 All tests passed! PostgreSQL is configured correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
