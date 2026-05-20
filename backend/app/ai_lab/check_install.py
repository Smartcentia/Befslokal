try:
    import semantic_kernel as sk
    print(f"✅ Semantic Kernel installed: {sk.__version__}")
except ImportError:
    print("❌ Semantic Kernel NOT installed")

try:
    from semantic_kernel.plugins.sessions import SessionsPythonTool
    print("✅ SessionsPythonTool found in 'semantic_kernel.plugins.sessions'")
except ImportError:
    print("⚠️ SessionsPythonTool NOT found in 'semantic_kernel.plugins.sessions' - Checking alternatives...")
    try:
        from semantic_kernel.core_plugins.sessions import SessionsPythonTool
        print("✅ SessionsPythonTool found in 'semantic_kernel.core_plugins.sessions'")
    except ImportError:
         print("❌ SessionsPythonTool NOT found. Package 'semantic-kernel-plugin-sessions' might be required or name is different.")
