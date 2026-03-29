"""Launch MARPLE Jupyter kernel."""

from ipykernel.kernelapp import IPKernelApp
from marple.jupyter.kernel import MARPLEKernel

IPKernelApp.launch_instance(kernel_class=MARPLEKernel)
