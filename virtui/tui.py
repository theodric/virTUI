import urwid
from .vm import list_vms, start_vm, shutdown_vm, destroy_vm, suspend_vm, resume_vm, has_serial_console, enter_console

class RestartTUI(Exception):
    """Raise this to force a full TUI restart/redraw after console."""

class VirTUI:
    def __init__(self):
        self.vms = []
        self.selected_vm_index = 0
        self.header = urwid.Text("virTUI - QEMU/KVM VM Manager", align='center')
        self.menu_bar = self.build_menu_bar()
        self.footer = urwid.Text("[Q]uit | [Enter] Actions | Arrows: Navigate", align='left')
        self.body_placeholder = urwid.WidgetPlaceholder(urwid.Filler(urwid.Text("Loading VMs...")))
        self.main_widget = urwid.Frame(
            body=self.body_placeholder,
            header=urwid.Pile([
                urwid.AttrMap(self.header, 'header'),
                self.menu_bar
            ]),
            footer=urwid.AttrMap(self.footer, 'footer')
        )
        self.palette = [
            ('header', 'white', 'dark blue'),
            ('footer', 'white', 'dark blue'),
            ('selected', 'white', 'dark red'),
            ('default', 'white', 'black'),
        ]
        self.loop = None
        self.refresh_vms()

    def build_menu_bar(self):
        # Boxed shortcut keys for clarity
        menu = urwid.Text("[S]tart | S[h]utdown | [D]estroy | S[u]spend | [R]esume | [C]onsole", align='left')
        return urwid.AttrMap(menu, 'header')

    def refresh_vms(self):
        self.vms = list_vms()
        self.update_ui()

    def update_ui(self):
        if not self.vms:
            widget = urwid.Filler(urwid.Text("No VMs found."))
        else:
            items = []
            for i, vm in enumerate(self.vms):
                # Use .value if available, else str(vm.state)
                state_val = getattr(vm.state, 'value', str(vm.state))
                if state_val == "ON":
                    state_disp = "RUNNING"
                elif state_val == "OFF":
                    state_disp = "SHUT OFF"
                elif state_val == "SUSPENDED":
                    state_disp = "SUSPENDED"
                else:
                    state_disp = state_val
                label = f"{vm.name} [{state_disp}]"
                if i == self.selected_vm_index:
                    items.append(urwid.AttrMap(urwid.Text(label), 'selected'))
                else:
                    items.append(urwid.AttrMap(urwid.Text(label), 'default'))
            listbox = urwid.ListBox(urwid.SimpleFocusListWalker(items))
            widget = listbox
        self.body_placeholder.original_widget = widget
        if self.loop:
            self.loop.draw_screen()

    def run(self):
        self.loop = urwid.MainLoop(
            self.main_widget,
            palette=self.palette,
            unhandled_input=self.handle_input
        )
        self.loop.run()

    def handle_input(self, key):
        if hasattr(self, 'action_menu') and self.action_menu is not None:
            # If action menu is open, handle its input
            if key in ('up', 'down'):
                self.action_menu.keypress((20, 1), key)
            elif key in ('enter',):
                self._perform_action(self.action_menu.focus_position)
            elif key in ('esc',):
                self._close_action_menu()
            return
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == 'up':
            if self.selected_vm_index > 0:
                self.selected_vm_index -= 1
                self.update_ui()
        elif key == 'down':
            if self.selected_vm_index < len(self.vms) - 1:
                self.selected_vm_index += 1
                self.update_ui()
        elif key in ('enter'):
            self._open_action_menu()
        # Universal boxed shortcuts for VM actions
        elif key in ('s', 'S'):
            self._universal_vm_action('Start')
        elif key in ('h', 'H'):
            self._universal_vm_action('Shutdown')
        elif key in ('d', 'D'):
            self._universal_vm_action('Destroy')
        elif key in ('u', 'U'):
            self._universal_vm_action('Suspend')
        elif key in ('r', 'R'):
            self._universal_vm_action('Resume')
        elif key in ('c', 'C'):
            self._universal_vm_action('Console')

    def _open_action_menu(self):
        vm = self.vms[self.selected_vm_index] if self.vms else None
        actions = [
            ('Start', start_vm),
            ('Shutdown', shutdown_vm),
            ('Destroy', destroy_vm),
            ('Suspend', suspend_vm),
            ('Resume', resume_vm),
        ]
        if vm and has_serial_console(vm.uuid):
            actions = [('Console', enter_console)] + actions
        self.action_menu_actions = actions
        menu_items = [urwid.Text('Select Action:'), urwid.Divider()]
        for label, _ in actions:
            menu_items.append(urwid.AttrMap(urwid.Text(label), None, 'selected'))
        self.action_menu = urwid.ListBox(urwid.SimpleFocusListWalker(menu_items[2:]))
        overlay = urwid.Overlay(
            urwid.LineBox(self.action_menu),
            self.main_widget,
            align='center', width=24,
            valign='middle', height=len(actions)+4
        )
        if self.loop:
            self.loop.widget = overlay
        self.footer.set_text("[Up/Down] Select | [Enter] Confirm | [Esc] Cancel")

    def _close_action_menu(self):
        self.action_menu = None
        if self.loop:
            self.loop.widget = self.main_widget
        self.footer.set_text("[Q]uit | [Enter] Actions | Arrows: Navigate")

    def _perform_action(self, action_index):
        if not self.vms:
            self._close_action_menu()
            return
        vm = self.vms[self.selected_vm_index]
        label, func = self.action_menu_actions[action_index]
        if label == 'Console':
            success = has_serial_console(vm.uuid)
            if not success:
                self.footer.set_text(f"No serial console available for {vm.name}")
                self._close_action_menu()
                return
            self._close_action_menu()
            self.footer.set_text(f"Attaching to console for {vm.name} (exit with Ctrl-] or Ctrl+C)")
            enter_console(vm.uuid)
            self.footer.set_text(f"Returned from console for {vm.name}")
            # Force a full TUI restart for a clean redraw
            raise RestartTUI()
            return
        else:
            success = func(vm.uuid)
            if not success:
                self.footer.set_text(f"Action '{label}' failed on {vm.name}")
            else:
                self.footer.set_text(f"Action '{label}' sent to {vm.name}")
            self._close_action_menu()
            self.refresh_vms()

    def _universal_vm_action(self, action_label):
        if not self.vms:
            self.footer.set_text("No VMs available.")
            return
        vm = self.vms[self.selected_vm_index]
        actions = {
            'Start': start_vm,
            'Shutdown': shutdown_vm,
            'Destroy': destroy_vm,
            'Suspend': suspend_vm,
            'Resume': resume_vm,
            'Console': enter_console,
        }
        if action_label == 'Console':
            if not has_serial_console(vm.uuid):
                self.footer.set_text(f"No serial console available for {vm.name}")
                return
            self.footer.set_text(f"Attaching to console for {vm.name} (exit with Ctrl-] or Ctrl+C)")
            enter_console(vm.uuid)
            self.footer.set_text(f"Returned from console for {vm.name}")
            # Force a full TUI restart for a clean redraw
            raise RestartTUI()
        else:
            func = actions[action_label]
            success = func(vm.uuid)
            if not success:
                self.footer.set_text(f"Action '{action_label}' failed on {vm.name}")
            else:
                self.footer.set_text(f"Action '{action_label}' sent to {vm.name}")
            self.refresh_vms() 