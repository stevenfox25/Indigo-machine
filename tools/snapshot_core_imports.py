# tools/snapshot_core_imports.py

def main():
    import indigo
    from indigo.api.app import create_app
    from indigo.services.runner import run_services

    print("=== CORE IMPORTS SNAPSHOT ===")
    print("indigo: OK")
    print("create_app: OK")
    print("run_services: OK")

if __name__ == "__main__":
    main()
