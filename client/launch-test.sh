#!/bin/bash

TARGET_URL='wss://naomi.hxat.hxtech.org/ws/notification'
TEST_DURATION=60
TEST_ARRIVALRATE=5
TEST_CHANNELS="${1:-3}"

for TARGET_INDEX in $(seq $TEST_CHANNELS)
do
    JSON_OVERRIDE="{\"config\": {\"phases\": [{\"duration\": $TEST_DURATION, \"arrivalRate\": $TEST_ARRIVALRATE}], \"target\": \"${TARGET_URL}/course-v1-HarvardX-HxAT101-2015-T${TARGET_INDEX}--04fe31c0-5fb8-4e2b-b644-0d7307abf399--1/\"}}"
    artillery run \
        -o report-hxat-12-${TARGET_INDEX}.json \
        --overrides "{\"config\": {\"phases\": [{\"duration\": $TEST_DURATION, \"arrivalRate\": $TEST_ARRIVALRATE}], \"target\": \"${TARGET_URL}/course-v1-HarvardX-HxAT101-2015-T${TARGET_INDEX}--04fe31c0-5fb8-4e2b-b644-0d7307abf399--1/\"}}" \
        connection-only.yml &
done
