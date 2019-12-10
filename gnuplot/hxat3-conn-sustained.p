set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H:%M:%S"

set title "hxat websockets load test (conn)"
set xlabel ARG2


plot ARG1 u 1:3 title "conn"

