set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H:%M:%S"

set title "hxat websockets load test (conn)"
set xlabel ARG1


plot "/vagrant/data/work/run1209/hxat-conn-sustained2.dat" u 1:3 title "conn"

