# samples on how to massage logs to make input for gnuplot

cat /var/log/syslog | grep WSDISCONNECT | cut -d ' ' -f 4 | uniq -c

cat /var/log/nginx/error.log | grep '\[error\]' | grep -v 'open\(\)' | grep premature | wc -lo

cat /var/log/nginx/error.log | grep '\[error\]' | grep -v 'open\(\)' | grep 'reset by peer'  | wc -l

ca error.log | grep 'reset by peer' | cut -d ' ' -f  2 | uniq -c > error-resetByPeer.dat
