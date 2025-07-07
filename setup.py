from setuptools import setup, find_packages

setup(
    name='virtui',
    version='0.1.0',
    description='A TUI for managing QEMU/KVM VMs',
    author='',
    packages=find_packages(),
    install_requires=[
        'urwid',
        'libvirt-python',
    ],
    entry_points={
        'console_scripts': [
            'virtui = virtui.main:main',
        ],
    },
    python_requires='>=3.7',
) 