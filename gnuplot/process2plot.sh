#!/bin/bash
#
# given a dir with hxat ws data, process logs to plot conn and fd graphs
#

xlabel=${1:-'10dec10'}
workdir=${2:-'/tmp'}

grep CONNECT "$workdir/syslog" | ./sustained-conn.py > "$workdir/sustained.data"
grep '\/annotation_store\/api\/' "$workdir/syslog" | grep -v middleware | cut -d ' ' -f 3,11,13 > "$workdir/request.data"
grep '\/annotation_store\/api\/' "$workdir/syslog" | grep ' 200' | cut -d ' ' -f 3,11,13 | uniq -c > "$workdir/request-success.data"
grep '\/annotation_store\/api\/' "$workdir/syslog" | grep ' 500' | cut -d ' ' -f 3,11,13 | uniq -c > "$workdir/request-failure.data"

grep 'reset by peer' "$workdir/error.log" | cut -d ' ' -f  2 | uniq -c > "$workdir/error-resetByPeer.data"
grep 'premature' "$workdir/error.log" | cut -d ' ' -f  2 | uniq -c > "$workdir/error-premature.data"
./merge-errors.py "$workdir/error-resetByPeer.data" "$workdir/error-premature.data" > "$workdir/error-merged.data"

cat "$workdir/access.log" | ./request-access.py > "$workdir/request-access.data"

gnuplot -c plot-conn-nofiles.p "$xlabel" "$workdir" > "$workdir"/plot-conn-nofiles.png
gnuplot -c plot-conn.p "$xlabel" "$workdir" > "$workdir"/plot-conn.png
gnuplot -c plot-nofiles.p "$xlabel" "$workdir" > "$workdir"/plot-nofiles.png
gnuplot -c plot-requests.p "$xlabel" "$workdir" > "$workdir"/plot-requests.png

