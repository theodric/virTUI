import urwid
from .tui import VirTUI, RestartTUI

def main():
    while True:
        tui = VirTUI()
        try:
            tui.run()
        except RestartTUI:
            continue
        break

if __name__ == "__main__":
    main() 