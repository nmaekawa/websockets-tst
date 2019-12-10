#!/bin/bash
#
# prog test_name #channels duration rate_per_sec
#


TARGET_HOSTNAME=''
TARGET_URL="wss://${TARGET_HOSTNAME}/ws/notification"
CONTEXTID=''
COLLECTIONID=''
SOURCEID=''

TEST_NAME="${1}"
TOTAL_CONN="${2:-20}"
RATE="${3:-1}"
SUSTAINED="${4:-10}"
WAVES="${5:-2}"
WAVES_INTERVAL="${6:-60}"

DURATION=$(echo "$TOTAL_CONN / $RATE" | bc)
THINK_TIME=$(echo "$DURATION + $SUSTAINED" | bc)
TOTAL_WAVE_TIME=$(echo "$THINK_TIME + $DURATION" | bc)
WAVE_SLEEP=$(echo "$TOTAL_WAVE_TIME + $WAVES_INTERVAL" | bc)
TOTAL_DURATION=$(echo "$WAVES*$WAVE_SLEEP" | bc)

echo
echo "starting test:"
echo "test_name($TEST_NAME)"
echo "total_conn($TOTAL_CONN)"
echo "rate($RATE)"
echo "sustained($SUSTAINED)"
echo "waves($WAVES)"
echo "interval($WAVES_INTERVAL)"
echo "duration($DURATION)"
echo "think_time($THINK_TIME)"
echo "total_wave_time($TOTAL_WAVE_TIME)"
echo "wave_sleep($WAVE_SLEEP)"
echo "total_duration($TOTAL_DURATION)"
echo

echo
echo "launch locust"
nohup /home/nmaekawa/venvs/locust/bin/locust --host https://${TARGET_HOSTNAME} --csv=${TEST_NAME} --no-web -c 1 -r 1 --run-time $TOTAL_DURATION > ${TEST_NAME}-locust 2>&1 &
echo "locust DONE"

echo
echo "launch artillery jobs"
for WAVE_NO in $(seq $WAVES)
do
    artillery run \
        -o ${TEST_NAME}-connection-${WAVE_NO}.json \
        --overrides "{\"config\": {\"phases\": [{\"duration\": $DURATION, \"arrivalRate\": $RATE}], \"target\": \"${TARGET_URL}/${CONTEXTID}${TARGET_INDEX}--${COLLECTIONID}--${SOURCEID}/\"}}" \
        -v "{\"think_time\": $THINK_TIME}" \
        connection-only.yml &
    echo
    echo "wave($WAVE_NO)  DONE"

    echo
    echo "about to sleep($WAVE_SLEEP) till next wave"
    sleep $WAVE_SLEEP
done


echo
echo "test launch DONE"

