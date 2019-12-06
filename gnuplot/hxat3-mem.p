set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H%M%S"

set title "hxat websockets load test (memory)"
set ylabel "MB"
set xlabel ARG2


#plot ARG1 u 1:5 title "used", ARG1 u 1:6 title "free", ARG1 u 1:7 title "avail"
plot ARG1 u 1:5 title "used"

