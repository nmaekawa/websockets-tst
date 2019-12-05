set terminal png size 2300,1000
set output 'run1204-mem.png'

set style data linespoint
set grid

p '../run1204/run1-hxat-stats.log' u 1:11

