from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Invitation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    receiver_email = models.EmailField()
    role = models.CharField(max_length=50)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)