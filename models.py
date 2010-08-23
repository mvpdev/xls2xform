from django.db import models
from django.core.files.storage import default_storage

class File(models.Model):
    file = models.FileField(upload_to="xls2xform/files/%Y%m%d%H%M%S", storage=default_storage) #")

    def name(self):
        return self.file.generate_filename()

class Submission(models.Model):
    file = models.ForeignKey(File)
    error_msg = models.CharField(max_length=100)

    def __unicode__(self):
        return self.file.name()

class XForm(models.Model):
    submission = models.ForeignKey(Submission)
    file = models.ForeignKey(File)
