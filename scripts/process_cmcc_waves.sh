# set_grid_unstructured
cdo setgrid,../../bin/cmcc_wave_grid cmcc_adrifs_waves_20230501.nc tmp1.nc
# spatial_interpolation
cdo remap,../../bin/remap_grid_ADRION,../../bin/weights/cmcc_waves_weights.nc tmp1.nc tmp2.nc
