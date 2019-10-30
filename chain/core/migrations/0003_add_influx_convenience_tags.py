# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import models, migrations
from chain.core.models import ScalarSensor
from chain.core.resources import influx_client
from django.utils.timezone import now
from datetime import datetime, timedelta
# from django.utils.dateparse import parse_datetime
from chain.influx_client import InfluxClient, HTTP_STATUS_SUCCESSFUL_WRITE
from django.db import IntegrityError
from sys import stdout

CHUNK_LIMIT = 10000
EPOCH = datetime(1970, 1, 1, 0, 0, 0)

def ms_to_dt(ms):
    return EPOCH + timedelta(milliseconds=ms)

def add_convenience_tags(apps, schema_editor):
    sensors = ScalarSensor.objects.all()
    print("\n\nMigrating data for {} sensors".format(len(sensors)))
    stdout.flush()
    for agg in ["", "_1h", "_1d", "_1w"]:
        measurement = influx_client._measurement + agg
        print("Migrating data from {} measurement...".format(measurement))
        stdout.flush()

        sensorsmigrated = 0
        datamigrated = 0
        for sensor in sensors:
            device = sensor.device
            site = device.site

            print("\rMigrating {} of {} sensors (requesting count)                  ".format(
                sensorsmigrated+1, len(sensors)), end='')
            stdout.flush()
            # doesn't really matter which column we use for the aggregates
            countcol = "value" if agg == "" else "mean"
            countdata = influx_client.get(
                "SELECT COUNT({}) FROM {} WHERE sensor_id = '{}' AND metric = ''".format(
                    countcol, measurement, sensor.id), True).json()
            assert len(countdata["results"]) == 1
            result = countdata["results"][0]
            assert len(result["series"]) == 1
            series = result["series"][0]
            assert len(series["columns"]) == 2
            assert len(series["values"]) == 1
            count = series["values"][0][series["columns"].index("count")]
            # select all this sensor's data that doesn't yet have a metric
            offset = 0
            while True:
                query = "SELECT * FROM {} WHERE sensor_id = '{}' AND metric = '' LIMIT {} OFFSET {}".format(
                    measurement, sensor.id, CHUNK_LIMIT, offset)

                print("\rMigrating {} of {} sensors (requesting data {} of {})                  ".format(
                    sensorsmigrated+1, len(sensors), offset+1, count), end='')
                stdout.flush()
                db_data = influx_client.get_values(influx_client.get(query, True, epoch="ms"))
                if len(db_data) == 0:
                    break
                print("\rMigrating {} of {} sensors (processing values for {} of {})             ".format(
                    sensorsmigrated+1, len(sensors), offset+1, count), end='')
                stdout.flush()
                if agg == "":
                    values = [d["value"] for d in db_data]
                    print("\rMigrating {} of {} sensors (processing timestamps for {} of {})             ".format(
                        sensorsmigrated+1, len(sensors), offset+1, count), end='')
                    stdout.flush()
                    try:
                        timestamps = [ms_to_dt(d["time"]) for d in db_data]
                    except:
                        print(d["time"])
                        raise
                    # TODO: I think under-the-hood this ends up converting back and forth
                    # between dict-of-arrays and array-of-dicts format, so there's some
                    # opportunity for optimizastion
                    print("\rMigrating {} of {} sensors (posting data {} of {})                ".format(
                        sensorsmigrated+1, len(sensors), offset+1, count), end='')
                    stdout.flush()
                    influx_client.post_data_bulk(site.id, device.id, sensor.id, sensor.metric, values, timestamps)
                    print(".", end='')
                    stdout.flush()
                else:
                    # import pdb
                    # pdb.set_trace()
                    query = ""
                    print("\rMigrating {} of {} sensors (building query for data {} of {})                ".format(
                        sensorsmigrated+1, len(sensors), offset+1, count), end='')
                    stdout.flush()
                    for data in db_data:
                        query += "{},sensor_id={},site_id={},device_id={},metric={} min={},max={},count={}i,sum={},mean={} {}".format(
                        measurement, sensor.id, site.id, device.id, sensor.metric,
                        data['min'], data['max'], data['count'], data['sum'], data['mean'],
                        InfluxClient.convert_timestamp(ms_to_dt(data['time']))) + "\n"

                    print("\rMigrating {} of {} sensors (posting data {} of {})                ".format(
                        sensorsmigrated+1, len(sensors), offset+1, count), end='')
                    stdout.flush()
                    response = influx_client.post('write', query)
                    if response.status_code != HTTP_STATUS_SUCCESSFUL_WRITE:
                        raise IntegrityError('Failed Query(status {}):\n{}\nResponse:\n{}'.format(
                            response.status_code, data, response.json()))
                offset += CHUNK_LIMIT
                datamigrated += len(db_data)

            sensorsmigrated += 1
        print("\nMigrated {} data points for measurement {}\n".format(datamigrated, measurement))
        stdout.flush()

# we don't actually need to remove the tags, they don't do any harm
def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20191017_1403'),
    ]

    operations = [
        migrations.RunPython(add_convenience_tags, noop)
    ]
