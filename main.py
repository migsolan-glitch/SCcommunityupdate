"""
Punto de Entrada Principal - Star Citizen Launcher & Localization Manager.
"""

import sys
import os

# Asegurar que el directorio actual esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import StarCitizenLauncherApp


def main():
    try:
        app = StarCitizenLauncherApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()
