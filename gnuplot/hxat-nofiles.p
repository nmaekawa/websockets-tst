set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H%M%S"

set title "hxat websockets load test (open files)"
set xlabel ARG2

plot ARG1 using 1:2 title "nginx", ARG1 using 1:5 title "daphne", ARG1 using 1:14 title "total"

