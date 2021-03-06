# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'XForm'
        db.create_table('xform_builder_xform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_string', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('latest_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='active_xform', null=True, to=orm['xform_builder.XFormVersion'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='xforms', to=orm['auth.User'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('xform_builder', ['XForm'])

        # Adding model 'XFormVersion'
        db.create_table('xform_builder_xformversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xform', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['xform_builder.XForm'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('base_section', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bversions', null=True, to=orm['xform_builder.XFormSection'])),
            ('qtypes_section', self.gf('django.db.models.fields.related.ForeignKey')(related_name='qversions', null=True, to=orm['xform_builder.XFormSection'])),
            ('id_stamp', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('version_number', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('xform_builder', ['XFormVersion'])

        # Adding model 'XFormSection'
        db.create_table('xform_builder_xformsection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('section_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('xform_builder', ['XFormSection'])

        # Adding M2M table for field versions on 'XFormSection'
        db.create_table('xform_builder_xformsection_versions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('xformsection', models.ForeignKey(orm['xform_builder.xformsection'], null=False)),
            ('xformversion', models.ForeignKey(orm['xform_builder.xformversion'], null=False))
        ))
        db.create_unique('xform_builder_xformsection_versions', ['xformsection_id', 'xformversion_id'])


    def backwards(self, orm):
        
        # Deleting model 'XForm'
        db.delete_table('xform_builder_xform')

        # Deleting model 'XFormVersion'
        db.delete_table('xform_builder_xformversion')

        # Deleting model 'XFormSection'
        db.delete_table('xform_builder_xformsection')

        # Removing M2M table for field versions on 'XFormSection'
        db.delete_table('xform_builder_xformsection_versions')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'xform_builder.xform': {
            'Meta': {'object_name': 'XForm'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_string': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'latest_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'active_xform'", 'null': 'True', 'to': "orm['xform_builder.XFormVersion']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'xforms'", 'to': "orm['auth.User']"})
        },
        'xform_builder.xformsection': {
            'Meta': {'object_name': 'XFormSection'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'section_json': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'versions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sections'", 'symmetrical': 'False', 'to': "orm['xform_builder.XFormVersion']"})
        },
        'xform_builder.xformversion': {
            'Meta': {'object_name': 'XFormVersion'},
            'base_section': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bversions'", 'null': 'True', 'to': "orm['xform_builder.XFormSection']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_stamp': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'qtypes_section': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'qversions'", 'null': 'True', 'to': "orm['xform_builder.XFormSection']"}),
            'version_number': ('django.db.models.fields.IntegerField', [], {}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['xform_builder.XForm']"})
        }
    }

    complete_apps = ['xform_builder']
