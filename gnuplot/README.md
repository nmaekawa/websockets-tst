# scripts to plot output from target/hxat-stats2.sh
#
# tested with gnuplot 5.2 patchlevel 2
# $> apt-get install gnuplot
#
# scripts expects to read from stdin and write to stdout
#

$> cat hxat.dat | gnuplot hxat-mem.p >> hxat-mem.png

