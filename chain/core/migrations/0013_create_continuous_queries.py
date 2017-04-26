# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from chain.core.resources import influx_client
from chain.localsettings import INFLUX_DATABASE, INFLUX_MEASUREMENT

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        influx_client.get('''
           CREATE CONTINUOUS QUERY "cq_1h" ON "{0}" 
               RESAMPLE EVERY 1h 
               BEGIN 
                   SELECT max("value"), min("value"), mean("value"), count("value") 
                   INTO "sensordata_1h" FROM "{1}" GROUP BY sensor_id,time(1h),*
               END
           '''.format(INFLUX_DATABASE, INFLUX_MEASUREMENT), True)

    def backwards(self, orm):
        "Write your backwards methods here."
        influx_client.get('DROP CONTINUOUS QUERY \"cq_1h\" on \"{}\"'.format(INFLUX_DATABASE), True)

    models = {
        u'core.device': {
            'Meta': {'ordering': "['name']", 'unique_together': "(['site', 'name', 'building', 'floor', 'room'],)", 'object_name': 'Device'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'building': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'floor': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'geo_location': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.GeoLocation']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'room': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'devices'", 'to': u"orm['core.Site']"})
        },
        u'core.geolocation': {
            'Meta': {'object_name': 'GeoLocation'},
            'elevation': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {})
        },
        u'core.metric': {
            'Meta': {'object_name': 'Metric'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'core.person': {
            'Meta': {'object_name': 'Person'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'geo_location': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.GeoLocation']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'picture_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'rfid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'people'", 'to': u"orm['core.Site']"}),
            'twitter_handle': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'core.presencedata': {
            'Meta': {'object_name': 'PresenceData'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presense_data'", 'to': u"orm['core.Person']"}),
            'present': ('django.db.models.fields.BooleanField', [], {}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presence_data'", 'to': u"orm['core.PresenceSensor']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'core.presencesensor': {
            'Meta': {'unique_together': "(['device', 'metric'],)", 'object_name': 'PresenceSensor'},
            'device': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presence_sensors'", 'to': u"orm['core.Device']"}),
            'geo_location': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.GeoLocation']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'presence_sensors'", 'to': u"orm['core.Metric']"})
        },
        u'core.scalardata': {
            'Meta': {'object_name': 'ScalarData', 'index_together': "[['sensor', 'timestamp']]"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scalar_data'", 'to': u"orm['core.ScalarSensor']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        u'core.scalarsensor': {
            'Meta': {'unique_together': "(['device', 'metric'],)", 'object_name': 'ScalarSensor'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sensors'", 'to': u"orm['core.Device']"}),
            'geo_location': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.GeoLocation']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sensors'", 'to': u"orm['core.Metric']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sensors'", 'to': u"orm['core.Unit']"})
        },
        u'core.site': {
            'Meta': {'object_name': 'Site'},
            'geo_location': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.GeoLocation']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'raw_zmq_stream': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        u'core.statusupdate': {
            'Meta': {'object_name': 'StatusUpdate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'status_updates'", 'to': u"orm['core.Person']"}),
            'status': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        u'core.unit': {
            'Meta': {'object_name': 'Unit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['core']
    symmetrical = True
