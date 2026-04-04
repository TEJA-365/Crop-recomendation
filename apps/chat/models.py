from django.db import models
from django.contrib.auth.models import User


class ChatConversation(models.Model):
    """
    Chat conversations between users and the AI assistant.
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('te', 'Telugu'),
        ('ta', 'Tamil'),
        ('kn', 'Kannada'),
        ('mr', 'Marathi'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    message = models.TextField(help_text="User's message")
    response = models.TextField(help_text="AI assistant's response")
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="Language of the conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Conversation"
        verbose_name_plural = "Chat Conversations"
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat - {self.user.username} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
