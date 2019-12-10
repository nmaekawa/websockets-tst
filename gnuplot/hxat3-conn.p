set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

set xdata time
set timefmt "%H:%M:%S"

set title "hxat websockets load test (conn)"
set xlabel ARG1


#plot "/vagrant/data/work/run1206/connect.dat" u 2:1 title "connect", "/vagrant/data/work/run1206/disconnect.dat" u 2:1 title "disconnect", "/vagrant/data/work/run1206/error-premature.dat" u 2:1 title "premature close", "/vagrant/data/work/run1206/error-resetByPeer.dat" u 2:1 title "reset by peer"
#plot "/vagrant/data/work/run1206/connect.dat" u 2:1 title "connect", "/vagrant/data/work/run1206/disconnect.dat" u 2:1 title "disconnect", "/vagrant/data/work/run1206/error-resetByPeer.dat" u 2:1 title "reset by peer"
plot "/vagrant/data/work/run1209/connect.dat" u 2:1 title "connect", "/vagrant/data/work/run1209/disconnect.dat" u 2:1 title "disconnect"

