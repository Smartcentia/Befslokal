# Alembic Migration Best Practices - BEFS Project

This document outlines best practices for creating safe, idempotent Alembic migrations that work across different database states (fresh databases, restored backups, etc.).

## 🎯 Core Principles

1. **Always check for existence before operations**
2. **Make all migrations idempotent** (safe to run multiple times)
3. **Never assume tables/columns exist from previous migrations**
4. **Test migrations against both fresh and restored databases**

---

## 🛠️ Common Patterns

### ✅ Creating Tables with Foreign Keys

**WRONG:**
```python
def upgrade():
    op.create_table(
        'child_table',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('parent_id', UUID, sa.ForeignKey('parent_table.id'))  # Assumes parent_table.id exists!
    )
```

**RIGHT:**
```python
def upgrade():
    conn = op.get_bind()

    # Check if parent column exists
    has_parent_id = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = 'parent_table'
                AND column_name = 'id'
        )
    """)).scalar()

    if has_parent_id:
        # Create table WITH FK
        op.create_table(
            'child_table',
            sa.Column('id', UUID, primary_key=True),
            sa.Column('parent_id', UUID, sa.ForeignKey('parent_table.id'))
        )
    else:
        # Create table WITHOUT FK
        op.create_table(
            'child_table',
            sa.Column('id', UUID, primary_key=True),
            sa.Column('parent_id', UUID)
        )
```

---

### ✅ Adding Columns to Existing Tables

**WRONG:**
```python
def upgrade():
    op.execute("ALTER TABLE properties ADD COLUMN external_data JSONB")  # Fails if table doesn't exist!
```

**RIGHT:**
```python
def upgrade():
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'properties'
            ) THEN
                ALTER TABLE properties ADD COLUMN IF NOT EXISTS external_data JSONB;
            END IF;
        END $$;
    """))
```

---

### ✅ Creating Indexes

**WRONG:**
```python
def upgrade():
    if 'my_table' not in existing_tables:
        op.create_table('my_table', ...)

    # Index created unconditionally - fails if table wasn't created!
    op.create_index('ix_my_table_name', 'my_table', ['name'])
```

**RIGHT:**
```python
def upgrade():
    if 'my_table' not in existing_tables:
        op.create_table('my_table', ...)

    # Index creation wrapped in existence check
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'my_table'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_my_table_name ON my_table(name);
            END IF;
        END $$;
    """))
```

---

### ✅ UPDATE Statements

**WRONG:**
```python
def upgrade():
    op.execute("UPDATE users SET active = TRUE WHERE created_at < NOW()")  # Fails if users doesn't exist!
```

**RIGHT - Check table existence:**
```python
def upgrade():
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN
                UPDATE users SET active = TRUE WHERE created_at < NOW();
            END IF;
        END $$;
    """))
```

**RIGHT - Check column type (when needed):**
```python
def upgrade():
    op.execute(text("""
        DO $$
        DECLARE
            col_type TEXT;
        BEGIN
            -- Get column type
            SELECT data_type INTO col_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name = 'active';

            -- Only update if column has expected type
            IF col_type = 'boolean' THEN
                UPDATE users SET active = TRUE WHERE active = FALSE;
            END IF;
        END $$;
    """))
```

---

## 📋 Migration Checklist

Before committing a new migration, verify:

- [ ] All `CREATE TABLE` statements use `IF NOT EXISTS` or check table existence
- [ ] All foreign key constraints check if target columns exist
- [ ] All `ALTER TABLE` statements wrapped in table existence checks
- [ ] All `CREATE INDEX` statements wrapped in table/column existence checks
- [ ] All `UPDATE`/`INSERT`/`DELETE` statements wrapped in table existence checks
- [ ] All operations are idempotent (safe to run multiple times)
- [ ] Both `upgrade()` and `downgrade()` functions are defensive
- [ ] Migration tested against:
  - [ ] Fresh database (no existing tables)
  - [ ] Database with partial schema (some tables exist)
  - [ ] Database with different column types (restored backup)

---

## 🚫 Anti-Patterns to Avoid

### 1. Assuming Migration Order
**Don't assume** that because migration A creates table X, migration B can reference table X without checks. The database might be restored from a backup where migration A never ran.

### 2. Unconditional Operations
**Never** run ALTER TABLE, UPDATE, CREATE INDEX, or FK creation without verifying prerequisites exist.

### 3. Type Assumptions
**Never assume** a column has a specific type. If you're updating based on boolean logic, check the column is actually boolean first.

### 4. Mixing Conditional and Unconditional
```python
# WRONG - table creation is conditional but index is not
if 'foo' not in existing_tables:
    op.create_table('foo', ...)
op.create_index('ix_foo', 'foo', ['name'])  # Fails if table wasn't created!
```

---

## 🧪 Testing Your Migrations

### Local Testing
```bash
# Test against fresh database
alembic upgrade head

# Test idempotency (should be safe to run twice)
alembic downgrade base
alembic upgrade head
alembic upgrade head  # Should not error

# Test against restored database
# 1. Restore Supabase backup to local Postgres
# 2. Run migrations
alembic upgrade head
```

### Pre-deployment Checklist
1. Run migrations locally against fresh database
2. Run migrations locally against restored Supabase backup
3. Check for any warnings or errors
4. Review all SQL statements being executed
5. Verify all operations have existence checks

---

## 🔧 Useful SQL Queries

### Check if Table Exists
```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'your_table'
);
```

### Check if Column Exists
```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
        AND table_name = 'your_table'
        AND column_name = 'your_column'
);
```

### Get Column Data Type
```sql
SELECT data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'your_table'
    AND column_name = 'your_column';
```

### Check if Constraint Exists
```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_schema = 'public'
        AND table_name = 'your_table'
        AND constraint_name = 'your_constraint'
);
```

---

## 📚 Examples from This Project

See these migrations for good examples of defensive patterns:
- `003_add_risk_assessment_tables.py` - Comprehensive table existence checks
- `add_email_verification_mfa.py` - Column type checking before UPDATE
- `6b2bea70fd4d_postgis_and_ns3451.py` - Complex conditional operations
- `004_add_external_data_column.py` - Multiple table checks in single migration
- `005_add_contract_filename_constraint.py` - Safe UPDATE with table checks

---

## 🆘 When Things Go Wrong

If a migration fails in production:
1. **Don't panic** - Alembic tracks which migrations have run
2. **Check Railway logs** for the exact error message
3. **Fix the migration** following patterns in this guide
4. **Test locally** against a restored database
5. **Deploy the fix** - Alembic will resume from where it failed

---

## 📝 Template for New Migrations

```python
"""Your migration description

Revision ID: xxxxx
Revises: xxxxx
Create Date: YYYY-MM-DD HH:MM:SS
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'xxxxx'
down_revision = 'xxxxx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All operations wrapped in existence checks
    op.execute(text("""
        DO $$
        BEGIN
            -- Check if target table exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'your_table'
            ) THEN
                -- Your operation here (ALTER TABLE, CREATE INDEX, etc.)
                ALTER TABLE your_table ADD COLUMN IF NOT EXISTS new_column VARCHAR;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    # Downgrade also needs existence checks
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'your_table'
            ) THEN
                ALTER TABLE your_table DROP COLUMN IF EXISTS new_column;
            END IF;
        END $$;
    """))
```

---

**Last Updated:** 2026-02-16
**Maintainer:** BEFS Development Team
