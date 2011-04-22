from django.db import models

from django.contrib.auth.models import User

class Xform(models.Model):
    xform_id = models.CharField(max_length=32)
    user = models.ForeignKey(related_name="xforms")
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)


