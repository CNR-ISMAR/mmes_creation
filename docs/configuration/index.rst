.. _configuration:

Configuration files
=====================



.. _gen_config:

General Configuration
+++++++++++++++++++++++

General configuration directives are stored in:guilabel:`config.json` file
The file has the following directives:

* **data_dir** root of your data dir see :ref:`dir_structure`
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


.. _proc_config:

Processing steps Configuration
+++++++++++++++++++++++++++++++

The processing steps for each model are defined in :guilabel:`processing.json` file.
You can edit the file and add the model system name to tha step of your interest under each variable group

The processing configuration file is composed by two section: :guilabel:`sea_level_prepare` and :guilabel:`waves_prepare`
when modify or adding new models the manage.py script help to add (or remove) the current model to each step.

Sea level prepare
-----------------

In this table are described the steps for sea level prepare

..  list-table:: Processing steps sea level
    :widths: auto
    :header-rows: 1

    * - JSON name
      - Description
      - Can be skipped if...
    * - variable_selection
      - Select only sea level variable
      - source model has only sea level variable: original variable name is setted in :ref:`src_config`
    * - temporal_interpolation
      - Temporal interpolation to match start, end and timesteps
      - source model has exact timesteps of the ensemble
    * - get_48hours
      - Get first 48hours of forecast model
      - source model is already 48hours long
    * - add_factor
      - Add a specific  offset factor (setted in :ref:`src_config` as ``sea_level_fact``) for this model to match reference level
      - the reference level is the same  of ensemble
    * - mask_before_interpolation
      - Add a mask to some part of the model before interpolation (values setted in :ref:`src_config`)
      - All values of source model are suitable
    * - spatial_interpolation
      - Interpolate to match same grid of the ensemble
      - already match same grid of the ensemble
    * - extrapolate_missing
      - Extrapolate missing values
      - No need to fill missing value in source model
    * - mask_after_interpolation
      - Add a mask to some part of the model after interpolation (values setted in :ref:`src_config`)
      - All values of source model are suitable
    * - mask_outside_area
      - Mask value outside area of interest
      - The extension of source model is the same of ensemble
    * - add_tide
      - Add astronomical tide model  to source forecast model
      - Forecast model already integrte tide.


Waves prepare
-----------------

..  list-table:: Processing steps waves
    :widths: auto
    :header-rows: 1

    * - JSON name
      - Description
      - Can be skipped if...
    * - merge_components
      - Merge multiple files from the source forecast to have allthe waves variables (Wave Significant Height, Wave period and Wave direction) in the same file.
      - Source forecast model already have the three variables in the same file.
    * - variable_selection
      - Select from source file only the three variables about waves (variable names setted in :ref:`src_config`) and rename them according to :guilabel:`ensemble_variables` in :guilabel:`config.json`.
      - The source file has only the variables about waves and
    * - invert_latitude
      - Invert latitude direction usng ``cdo invertlat`` command
      - The latitude is already coherent with the ensemble
    * - set_miss_value
      - Fill missing value with ``cdo setmissval`` . Missing value is setted in :ref:`src_config` (``miss_value``)
      - The source forecast
    * - change_int_float
      - Change data type of variables integer  float
      - Data type for all variables are already float
    * - temporal_interpolation
      - Temporal interpolation to match start, end and timesteps
      - source model has exact timesteps of the ensemble
    * - get_48hours
      - Get 48hours
      - Step description
    * - set_grid_unstructured
      - Set grid unstructured
      - Step description
    * - spatial_interpolation
      - Spatial interpolation
      - Step description
    * - extrapolate_missing
      - Extrapolate missing value with ```cdo fillmiss```
      - Step description
    * - mask_after_interpolation
      - Add a mask to some part of the model after interpolation (values setted in :ref:`src_config`)
      - All values of source model are suitable
    * - mask_outside_area
      - Mask value outside area of interest
      - The extension of source model is the same of ensemble
    * - remove_zero_values
      - Remove values setted to zero and replace with missing value
      - No data values are setted correctly




