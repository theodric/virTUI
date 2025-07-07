# virTUI
like virt-manager (lite) but for the terminal  
like [haTUI](https://github.com/theodric/hatui) but for qemu-kvm  
_Python + urwid_  

![screenshot](/screenshot.png)

Believe me, I wanted to add a lot more features and polish, and I did, but completely pathological things like reordering menus or adding help text or (God forbid) context-sensitive menu contents all caused the TUI to completely fail to render after coming back from a console session, and _I_ need the console session capability, so all the fancy colors and niceties went away. ** Pull requests welcome! **

## Installation

```sh
pip install .
# or possibly
pip install --break-system-packages .
```

## Run

```sh
virtui
```
