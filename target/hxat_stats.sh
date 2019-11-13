#!/bin/bash
# crontab suggestion, for data point every 15sec
# * * * * * /home/nmaekawa/bin/hxat_stats.sh >> /home/nmaekawa/hxat_stats.log
# * * * * * (sleep 15; /home/nmaekawa/bin/hxat_stats.sh >> /home/nmaekawa/hxat_stats.log)
# * * * * * (sleep 30; /home/nmaekawa/bin/hxat_stats.sh >> /home/nmaekawa/hxat_stats.log)
# * * * * * (sleep 45; /home/nmaekawa/bin/hxat_stats.sh >> /home/nmaekawa/hxat_stats.log)

#
# observed that, at times, either nginx or daphne launches an extra process for
# a few seconds, and that messes up the columns in the output data file.
# trying to mitigate that with hxat_stats2.sh which sums the stats of all
# process for each program.
#
# todo:
#   - maybe log to 2 files and resolve this in gnuplot
#

# collect pids; do you need to sort?
NAOMI_PIDS=''
for process in nginx daphne
do
    x=$(ps -ef | grep ${process} | grep -v grep | awk '{print $2}')
    NAOMI_PIDS="$NAOMI_PIDS $x"
done

# check mem, cpu, open files per pid
for pid in $NAOMI_PIDS
do
    open_files=$(lsof -p $pid | wc -l )
    mem_cpu=$(ps -p $pid -o %mem=,%cpu=)
    row="$row $open_files $mem_cpu"
done

echo "$(date +'%H%M%S') $row"
