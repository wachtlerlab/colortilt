#!/bin/bash

tstamp=$(date +%Y%m%dT%H%M)
echo "Time: $tstamp"
DIR="$tstamp"
mkdir "$DIR"

echo "[p] paper figures"
echo "[p] Figure 2"
./ct-load.py "$EXPFILE" | ./ct-ana.py | ./ct-filter.py -B 0.0 | ./ct-plot.py --ylim 35 --single --no-title -S -W 16 -H 12 -P "$DIR" -F shift_all_single_0.eps 2>> log.tmp

echo "[p] Figure 3"
./ct-load.py "$EXPFILE" | ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-conv.py abs-shift | ./ct-spread.py --max-spread  > "$DIR/maxspread.csv"
./ct-load.py $EXPFILE | ./ct-ana.py -C | ./ct-plot.py --scale 2 -W 5.75 -H 4 -S -U in --ylim 30 --no-title -P "$DIR"  -F shift_all.eps --annotate "$DIR/maxspread.csv" 2>> log.tmp

echo "[p] Figure 4"
./ct-load.py "$EXPFILE" | ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-conv.py abs-shift | ./ct-spread.py --sizerel | ./ct-plot.py -S -F sizerel.eps -P "$DIR" -U in -W 5.75 -H 7 2>> log.tmp

echo "[p] Figure 5"
./ct-load.py "$EXPFILE" | ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-conv.py abs-shift | ./ct-spread.py --sizerel | ./ct-slope.py --method mean size | ./ct-plot.py --no-legend -S -F "slope28.eps" -P "$DIR" -U in -W 5.75 -H 5.75 --scale 0.5 --daylight 2>> log.tmp
./ct-load.py "$EXPFILE" | ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-conv.py abs-shift | ./ct-spread.py --sl-rel 40 | ./ct-slope.py --method mean size | ./ct-plot.py --no-legend -S -F "slope28rel.eps" -P "$DIR" -U in -W 5.75 -H 5.75 --scale 0.5 2>> log.tmp
