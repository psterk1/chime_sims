

#!/bin/bash

# Set the arguments
chains=8 #
n_iters=5000
burn_in=2000
reopen_day=71 # day social distancing restrictions lifting
reopen_speed=.05 #
reopen_cap=.2 #


python _01_GOF_sims.py \
    -p data/CCH_parameters.csv \
    -t data/CCH_ts.csv \
    -C $chains \
    -b \
    --penalty .25 \
    -i $n_iters \
    -B $burn_in \
    --reopen_day $reopen_day \
    --reopen_speed $reopen_speed \
    --reopen_cap $reopen_cap \
    --prefix CCH \
    -o flexB_novent \
    --ignore_vent

