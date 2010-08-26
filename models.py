#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
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
        """For downloading XForms we want this path to be relative to
        the app directory."""
        m = re.search(r"xls2xform(.*)", self.file.path)
        assert m, "This XForm isn't stored in the app directory: " + self.file.path
        return m.group(0)
