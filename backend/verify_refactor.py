
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

print("Verifying imports...")

try:
    print("Checking app.services.intelligence...")
    import app.services.intelligence
    print("OK")
    
    print("Checking app.services.analytics...")
    import app.services.analytics
    print("OK")
    
    print("Checking app.services.search...")
    import app.services.search
    print("OK")

    print("Checking app.services.infrastructure...")
    import app.services.infrastructure
    print("OK")
    
    print("Checking app.services.external...")
    import app.services.external
    print("OK")

    # Check commonly used modules that might import the above
    print("Checking app.main...")
    import app.main
    print("OK")

except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)

print("\n✅ All core modules import successfully!")
