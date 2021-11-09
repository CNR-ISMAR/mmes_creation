.. _configuration:

Configuration files
=====================

.. _src_config:

Suorce Configuration
+++++++++++++++++++++

Source list are stored by default in the :guilabel:`sources.json` file in the root directory, the filename can be customized in general config :guilabel:`config.json`

Refer to :guilabel:`source_template.json` to create your own configuration file.

If the ensemble creation for sea_level include models that need to add tide to express total sea level we suggest to put the tide source in the first place of config file.

You can also run from command line:

    ```
    python manage.py new
    ```

This  will start a *step by step* procedure to create a new sources.json file. If something goes wrong you'll find a convenient backup of your last configuration on sources.json.bak


.. _gen_config:

General Configuration
+++++++++++++++++++++++

General configuration directives are stored in:guilabel:`config.json` file
The file has the following directives:

* **data_dir** root of your data dir see :ref:`introduction`
* **sources_file** name of sources config file (default: *sources.json*)
* **ensemble_name** name of the enemble yo're going to create, this name will used for filenames
* **ensemble_variables** a JSON objects with the variable of each ensemble file (will be used in filename) and the related array for variable names in the final NetCDF file. Please note that the original variables of each forecast will be renamed following this order according to the processing.json file
* **mask_file** name of final grid of ensemble, all value outside this mask will be set to nodata
* **gap_days** max umber of days that will be attempted to be automatically gap-filled: check the output at least every n days



Default config.json::

    {
    "data_dir": "/usr3/iwsdata",
    "sources_file": "sources.json",
    "ensemble_name": "TMES",
    "ensemble_variables": {"sea_level": ["sea_level"], "waves": ["whs", "wmp", "wmd"]},
    "mask_file": "{data_dir}/config/mask/TMES_mask_002_ext.nc",
    "gap_days":  "5"
    }


The config value will be loaded **recursively** by loadconfig() function so in the file you can use previously declared values between curly brackets such as {data_dir} that will be replaced by the actual **data_dir** value.

.. _proc_config:

The processing steps for each model are defined in :guilabel:`processing.json` file.
You can edit the file and add the model system name to tha step of your interest under each variable group

[comment]: # TO DO change instructions when add procedure to manage.py

