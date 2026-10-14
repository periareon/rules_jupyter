"""Launch an IPython kernel.

A minimal kernel executable used to exercise `jupyter_kernelspec` without
requiring additional language toolchains.
"""

from ipykernel import kernelapp

if __name__ == "__main__":
    kernelapp.launch_new_instance()
