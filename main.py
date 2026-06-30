import sys
import os

# Đảm bảo đường dẫn module được nhận diện
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from gui.main_window import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
