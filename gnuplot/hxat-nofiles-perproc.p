set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid

p '/dev/stdin' u 1:2, '/dev/stdin' u 1:5, '/dev/stdin' u 1:8

