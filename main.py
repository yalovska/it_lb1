import tkinter as tk
from gui import DatabaseGUI

def main():
    root = tk.Tk()
    app = DatabaseGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()