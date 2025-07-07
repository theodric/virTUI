import libvirt
from enum import Enum
import sys
import os
import subprocess
import xml.etree.ElementTree as ET

# Set this to True to enable debug logging
DEBUG = False

class VMState(Enum):
    RUNNING = 'ON'
    SHUTOFF = 'OFF'
    SUSPENDED = 'SUSPENDED'
    UNKNOWN = 'UNKNOWN'

class VMAction(Enum):
    START = 'start'
    SHUTDOWN = 'shutdown'
    DESTROY = 'destroy'
    SUSPEND = 'suspend'
    RESUME = 'resume'
    CONSOLE = 'console'

class VM:
    def __init__(self, name, state, uuid):
        self.name = name
        self.state = state
        self.uuid = uuid


def list_vms():
    debug_log_path = os.path.join(os.path.dirname(__file__), '..', 'virtui_debug.log')
    def log_debug(msg):
        if DEBUG:
            with open(debug_log_path, 'a') as f:
                f.write(msg + '\n')
    conn = libvirt.open("qemu:///system")
    vms = []
    try:
        domains = conn.listAllDomains()
        log_debug(f"[DEBUG] Found {len(domains)} domains")
        for dom in domains:
            log_debug(f"[DEBUG] Domain: {dom.name()} (UUID: {dom.UUIDString()})")
            state, _ = dom.state()
            vms.append(VM(dom.name(), _state_to_enum(state), dom.UUIDString()))
    except Exception as e:
        log_debug(f"[DEBUG] Exception in list_vms: {e}")
    finally:
        conn.close()
    return vms

def _state_to_enum(state):
    # libvirt.VIR_DOMAIN_* constants
    if state == libvirt.VIR_DOMAIN_RUNNING:
        return VMState.RUNNING
    elif state == libvirt.VIR_DOMAIN_SHUTOFF:
        return VMState.SHUTOFF
    elif state == libvirt.VIR_DOMAIN_PAUSED:
        return VMState.SUSPENDED
    else:
        return VMState.UNKNOWN 

def start_vm(uuid):
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        dom.create()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def shutdown_vm(uuid):
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        dom.shutdown()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def destroy_vm(uuid):
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        dom.destroy()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def suspend_vm(uuid):
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        dom.suspend()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def resume_vm(uuid):
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        dom.resume()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def has_serial_console(uuid):
    debug_log_path = os.path.join(os.path.dirname(__file__), '..', 'virtui_debug.log')
    def log_debug(msg):
        if DEBUG:
            with open(debug_log_path, 'a') as f:
                f.write(msg + '\n')
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        xml = dom.XMLDesc()
        root = ET.fromstring(xml)
        for console in root.findall('.//devices/console'):
            if console.get('type') in ('pty', 'serial'):
                log_debug(f"[DEBUG] VM {dom.name()} has serial console: {ET.tostring(console, encoding='unicode')}")
                return True
        log_debug(f"[DEBUG] VM {dom.name()} has no serial console")
        return False
    except Exception as e:
        log_debug(f"[DEBUG] Exception in has_serial_console: {e}")
        return False
    finally:
        conn.close()

def enter_console(uuid):
    debug_log_path = os.path.join(os.path.dirname(__file__), '..', 'virtui_debug.log')
    def log_debug(msg):
        if DEBUG:
            with open(debug_log_path, 'a') as f:
                f.write(msg + '\n')
    conn = libvirt.open("qemu:///system")
    try:
        dom = conn.lookupByUUIDString(uuid)
        name = dom.name()
        log_debug(f"[DEBUG] Launching virsh console {name}")
        # Clear the terminal before entering console
        os.system('clear')
        subprocess.run(["virsh", "console", name])
        return True
    except Exception as e:
        log_debug(f"[DEBUG] Exception in enter_console: {e}")
        return False
    finally:
        conn.close() 