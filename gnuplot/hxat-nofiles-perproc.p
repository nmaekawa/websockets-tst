set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

p '../run1204/run1-hxat-stats.log' u 1:2, '../run1204/run1-hxat-stats.log' u 1:5, '../run1204/run1-hxat-stats.log' u 1:8

