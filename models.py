from django.db import models
from django.core.files.storage import default_storage

file_options = { "upload_to" : "xls2xform/submissions/%Y%m%d%H%M%S",
                 "storage" : default_storage, }

class Submission(models.Model):
    file = models.FileField(**file_options)
    error_msg = models.TextField()
    private = models.BooleanField(default=True)

class XForm(models.Model):
    submission = models.ForeignKey(Submission)
    file = models.FileField(**file_options)

	def __unicode__(self):
		return self.uri()

	def uri(self):
		return re.sub(r"^/(.*xls2xform.files)/", "/xform_files/", self.file.path)
