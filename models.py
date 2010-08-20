from django.db import models

class Submission(models.Model):
    file = models.FileField(upload_to="./submissions") #/%Y%m%d%H%M%S")
    error_msg = models.CharField(max_length=100)

class XForm(models.Model):
    submission = models.ForeignKey(Submission)
    text = models.TextField()
