set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H:%M:%S"

set title "hxat websockets load test"
set xlabel ARG1

filename(n) = sprintf("%s/%s", ARG2, n)

plot filename("cron.log") using 2:3 title "nginx", filename("cron.log") using 2:4 title "daphne", filename("cron.log") using 2:5 title "total", filename("error-merged.data") using 1:2 title "error", filename("sustained.data") using 1:3 title "conn"

