Debugging
======================

1. "Failed to open USB device" error.
Usually this can be solved if you unplug the USB cable and re-plug the DYNAP-SE1 board to your machine. If not, it's probably due to the installation. You should update your udev rules by doing the following.

* Make a file in /etc/udev/rules.d/ called 60-inilabs.rules

.. code-block:: bash

    cd /etc/udev/rules.d
    cat 60-inilabs.rules

* Put the lines below into this file:

.. code-block:: 

    # All DVS/DAVIS/Dynap-se systems
    SUBSYSTEM=="usb", ATTR{idVendor}=="152a", ATTR{idProduct}=="84[0-1]?", MODE="0666"

* Then, you run this command:

.. code-block:: bash

    udevadm control --reload-rules