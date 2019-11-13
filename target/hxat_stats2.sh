#!/bin/bash
# crontab suggestion, for data point every 15sec
# * * * * * /home/nmaekawa/bin/hxat_stats2.sh >> /home/nmaekawa/hxat_stats2.log
# * * * * * (sleep 15; /home/nmaekawa/bin/hxat_stats2.sh >> /home/nmaekawa/hxat_stats2.log)
# * * * * * (sleep 30; /home/nmaekawa/bin/hxat_stats2.sh >> /home/nmaekawa/hxat_stats2.log)
# * * * * * (sleep 45; /home/nmaekawa/bin/hxat_stats2.sh >> /home/nmaekawa/hxat_stats2.log)

#
# printing totals of open files, mem, cpu for nginx and daphne processes
# the calculation does take time, log shows time shifted by 1sec
#
# todo: try to do calculations in gnuplot
#

# collect pids; do you need to sort?
NGINX_PIDS=$(ps -ef | grep nginx | grep -v grep | awk '{print $2}')
DAPHNE_PIDS=$(ps -ef | grep daphne | grep -v grep | awk '{print $2}')

# check mem, cpu, open files for nginx
total_open=0
total_mem=0.0
total_cpu=0.0
for pid in $NGINX_PIDS
do
    open_files=$(lsof -p $pid | wc -l )
    total_open=$(echo "$total_open + $open_files" | bc) 
    mem=$(ps -p $pid -o %mem=)
    total_mem=$(echo "$total_mem + $mem" | bc)
    cpu=$(ps -p $pid -o %cpu=)
    total_cpu=$(echo "$total_cpu+$cpu" | bc)
done
nginx_row="$total_open $total_mem $total_cpu"

# check mem, cpu, open files for daphne
total_open=0
total_mem=0.0
total_cpu=0.0
for pid in $DAPHNE_PIDS
do
    open_files=$(lsof -p $pid | wc -l )
    total_open=$(echo "$total_open+$open_files" | bc) 
    mem=$(ps -p $pid -o %mem=)
    total_mem=$(echo "$total_mem+$mem" | bc)
    cpu=$(ps -p $pid -o %cpu=)
    total_cpu=$(echo "$total_cpu+$cpu" | bc)
done
daphne_row="$total_open $total_mem $total_cpu"


echo "$(date +'%H%M%S') $nginx_row $daphne_row"
