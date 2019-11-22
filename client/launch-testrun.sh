#!/bin/bash

TARGET_HOSTNAME=''
TARGET_URL="wss://${TARGET_HOSTNAME}/ws/notification"
CONTEXTID=""
COLLECTIONID=""
SOURCEID=""

TEST_RUN="${1}"
TEST_CHANNELS="${2:-3}"

# this rate launches 300 connections total (in 1 min)
TEST_DURATION=60
TEST_ARRIVALRATE=5

echo
echo "launch artillery jobs"
for TARGET_INDEX in $(seq $TEST_CHANNELS)
do
    artillery run \
        -o ${TEST_RUN}-connection-${TARGET_INDEX}.json \
        --overrides "{\"config\": {\"phases\": [{\"duration\": $TEST_DURATION, \"arrivalRate\": $TEST_ARRIVALRATE}], \"target\": \"${TARGET_URL}/${CONTEXTID}${TARGET_INDEX}--${COLLECTIONID}--${SOURCEID}/\"}}" \
        connection-only.yml &
done


sleep 40
#
# launch websocat in a separate shell, before this script
#
#echo
#echo "launch websocat"
#nohup websocat --no-close -k "${TARGET_URL}/${CONTEXTID}--${COLLECTIONID}--${SOURCEID}/" > ${TEST_RUN}-received.txt 2>&1 &

sleep 5
echo
echo "launch locust"
nohup /home/nmaekawa/venvs/locust/bin/locust --host https://${TARGET_HOSTNAME} --csv=${TEST_RUN} --no-web -c 1 -r 1 --run-time 210 > ${TEST_RUN}-locust 2>&1 &

echo
echo "done launching test"
jobs

