# tools/snapshot_settings.py

from indigo.config.settings import get_settings

def main():
    s = get_settings()
    print("=== SETTINGS SNAPSHOT ===")
    print(f"ENABLE_API={s.ENABLE_API}")
    print(f"ENABLE_UI={s.ENABLE_UI}")
    print(f"SIMULATION_MODE={s.SIMULATION_MODE}")
    print(f"POLL_HZ={s.POLL_HZ}")

if __name__ == "__main__":
    main()
