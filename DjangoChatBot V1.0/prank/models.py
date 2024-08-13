from django.db import models
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

class Assistant(models.Model):
    name = models.CharField(max_length=100)
    role = models.TextField()

    def __str__(self):
        return self.name

class ChatSession(models.Model):
    id = models.CharField(max_length=20, primary_key=True)  # Use CharField for custom IDs
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, null=True)  # Allow blank and null values
    start_time = models.DateTimeField(auto_now_add=True)
    last_visited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} for {self.user.username}"

class ChatHistory(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(default = 0)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.number} - {self.timestamp}"

    @staticmethod
    def get_next_number(session):
        # Get the last message number for the given session
        last_message = ChatHistory.objects.filter(session=session).order_by('-number').first()
        if last_message:
            return last_message.number + 1
        else:
            return 0
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")