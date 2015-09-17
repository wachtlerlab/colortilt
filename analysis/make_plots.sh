#!/bin/bash

EXPFILE=../../colortilt-data/experiment

tstamp=$(date +%Y%m%dT%H%M)
echo "Time: $tstamp"
DIR="$tstamp"
mkdir "$DIR"


#func do all analysis

make_shift_plots() {
    ./ct-load.py "$EXPFILE" "$1" | ./ct-ana.py -C | ./ct-plot.py -S -P "$DIR" -W 60 -H 40 --ylim 35 2>> log.tmp
    ./ct-load.py "$EXPFILE" "$1" | ./ct-ana.py -C --col=duration | ./ct-plot.py -S -P "$DIR" -W 60 -H 40 2>> log.tmp

    ./ct-load.py "$EXPFILE" "$1" |  ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-conv.py rel2abs | ./ct-plot.py --vertical -S -P "$DIR" -W 20 -H 60 --ylim 35 2>> log.tmp

    ./ct-load.py "$EXPFILE" "$1" | ./ct-conv.py rel2abs | ./ct-ana.py -C -M | ./ct-plot.py -S -P "$DIR" 2>> log.tmp
    ./ct-load.py "$EXPFILE" "$1" | ./ct-ana.py -C -M | ./ct-plot.py -S -P "$DIR" 2>> log.tmp

    ./ct-load.py "$EXPFILE" "$1" | ./ct-filter.py --no-control | ./ct-conv.py rel2abs | ./ct-ana.py -C | ./ct-spread.py | ./ct-plot.py --vertical -W 20 -H 60 -S -P "$DIR" 2>> log.tmp
}


# read in subjects
while IFS= read -r; do
    subjects+=("$REPLY")
done < <(./ct-load.py ../../colortilt-data/experiment | ./ct-ana.py | ./ct-N.py --subjects)
[[ $REPLY ]] && subjects+=("$REPLY")


for subject in "${subjects[@]}"; do
    echo "[p] shift: '$subject'"
    make_shift_plots "$subject" 2>> log.tmp
done

echo "[p] shift *"
make_shift_plots

echo "[p] sizerel"
./ct-load.py "$EXPFILE" | ./ct-ana.py | ./ct-sizerel.py | ./ct-plot.py -S -P "$DIR" -W 20 -H 32 2>> log.tmp
./ct-load.py "$EXPFILE" | ./ct-filter.py --fg-sign='+' | ./ct-ana.py | ./ct-sizerel.py | ./ct-plot.py -F 'sizerel-pos.pdf' -S -P "$DIR" -W 20 -H 32 2>> log.tmp
./ct-load.py "$EXPFILE" | ./ct-filter.py --fg-sign='-' | ./ct-ana.py | ./ct-sizerel.py | ./ct-plot.py -F 'sizerel-neg.pdf' -S -P "$DIR" -W 20 -H 32 2>> log.tmp

echo "[p] spread-sizrel:"
./ct-load.py "$EXPFILE" | ./ct-filter.py --no-control | ./ct-ana.py -C | ./ct-spread.py --sizerel | ./ct-plot.py -F "sizerel-spread.pdf" -S -P "$DIR" -W 20 -H 32 2>> log.tmp

echo "[p] scat"
./ct-load.py "$EXPFILE" | ./ct-ana.py -C | ./ct-scat.py | ./ct-plot.py -S -P "$DIR" -W 32 -H 20 2>> log.tmp

echo "[p] old vs. new"
./ct-load.py "$EXPFILE" twachtler | ./ct-ana.py | ./ct-cmpold.py --inner twachtler allmatchesTW.csv | ./ct-plot.py -S -P "$DIR" -W 60 -H 40 --ylim 35 2>> log.tmp

sudo "[p] paper figures"
./ct-load.py "$EXPFILE" | ./ct-ana.py | ./ct-filter.py -B 0.0 | ./ct-plot.py --ylim 35 --single --no-title -S -W 16 -H 12 -F shift_all_single_0.pdf 2>> log.tmp
./ct-load.py "$EXPFILE" twachtler | ./ct-ana.py | ./ct-cmpold.py --inner twachtler allmatchesTW.csv | ./ct-filter.py -B 0.0 | ./ct-plot.py --ylim 35 --single --no-title -S -F twctcmp.pdf -W 16 -H 12 2>> log.tmp

echo "Plots:"
ls "$DIR"
echo "All done."
