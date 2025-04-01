import sys
import logging

from .view.gui import CalcApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

if __name__ == '__main__':
    app = CalcApp(sys.argv)
    sys.exit(app.exec())