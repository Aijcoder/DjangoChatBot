from django.contrib import admin
from .models import Assistant, ChatSession, ChatHistory

@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ('name', 'role')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'assistant', 'title', 'start_time', 'last_visited')
    list_filter = ('user', 'assistant', 'start_time')
    search_fields = ('id', 'title', 'user__username')

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('session', 'number', 'message', 'timestamp')
    list_filter = ('session', 'number', 'timestamp')
    search_fields = ('message','number')
