set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H%M%S"

set title "hxat websockets load test"
set ylabel "KB"
set xlabel ARG2


plot ARG1 using 1:11 title "total used mem"

