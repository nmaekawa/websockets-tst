set terminal png size 2300,1000
set output '/dev/stdout'

set style data point
set grid

set xdata time
set timefmt "%H:%M:%S"

set title "hxat websockets load test"
set xlabel ARG1

filename(n) = sprintf("%s/%s", ARG2, n)

plot filename("request-success.data") using 2:1 title "success" , filename("request-failure.data") using 2:1 title "failure", filename("request-access.data") using 1:2 title "http success", filename("request-access.data") using 1:3 title "http failure", filename("request-access.data") using 1:4 title "ws success", filename("request-access.data") using 1:5 title "ws failure",

