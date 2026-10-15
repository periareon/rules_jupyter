# The Jupyter kernel entrypoint. Jupyter passes the connection file as the
# only argument, exactly as the kernelspec installed by `IJulia.installkernel`
# would (`julia -e "import IJulia; IJulia.run_kernel()" {connection_file}`).
import IJulia

IJulia.run_kernel()
