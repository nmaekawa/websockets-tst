set terminal png size 2300,1000
set output '/dev/stdout'

set style data linespoint
set grid
set xdata time
# cat access.log | cut -d ':' -f 2-3  | uniq -c > access-daily-perminute.dat
#set timefmt "%M:%S"

# cat access.log | cut -d ' ' -f 4 | cut -d ':' -f 1-2 | uniq -c > access-perhour.dat
set timefmt "[%d/%b/%Y:%H"

p '/dev/stdin' u 2:1

