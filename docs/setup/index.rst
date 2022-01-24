Installation
============

The software i sintended to run aona GNU/linux based server

1. Create a python `virtualenv <https://docs.python.org/3/library/venv.html>`_ and activate it.

.. code:: bash

    python3 -m venv /path/to/new/virtual/environment/mmes
    source activate /path/to/new/virtual/environment/mmes/bin/activate


2. Clone this repository in a convenient location.

.. code:: bash

    git clone git@github.com:CNR-ISMAR/mmes.git

3. Install requirements with

.. code:: bash

    pip install -r requirements.txt


4. Prepare the data directory structure according to the :ref:`dir_structure` section.

.. code:: bash

    python manage.py dir



5. Manually edit the general configuration file :guilabel:`config.json` according to your needs (see :ref:`gen_config`) section.


6. From the main directory launch

.. code:: bash

    python manage.py new

to create a new source config file or

.. code:: bash

    python manage.py mod

to edit existing source config file.
Refer to :ref:`configuration` section fro detailed information about config files

7. For each source forecast  you need to add the model name to required step in :guilabel:`processing.json` :ref:`proc_config`