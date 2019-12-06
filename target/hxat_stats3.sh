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
REDIS_PIDS=$(ps -ef | grep redis | grep -v grep | awk '{print $2}')

# check mem, cpu, open files for nginx
nginx_files=$(lsof | grep nginx | wc -l )
daphne_files=$(lsof | grep daphne | wc -l )


#total_avg_cpu=$(top -bn1 | grep load | awk '{printf "%.2f\n", $(NF-2)}')
total_mem=$(free --mega | grep Mem | awk '{print $3,$4,$7}')
total_files=$(lsof | wc -l)

echo "$(date +'%H%M%S') $nginx_files $daphne_files $total_files $total_mem"
