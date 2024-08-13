import csv
import json
import random
import string

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .forms import SignUpForm
from .models import Assistant, ChatHistory, ChatSession
from .openai_client import get_openai_response

def generate_session_id():
    return 'pr' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def home(request):
    if request.user.is_authenticated:
        last_login = request.user.last_login
        if last_login and timezone.now() - last_login <= timezone.timedelta(weeks=1):
            return redirect('profile')
    return render(request, 'prank/home.html')

def latest_chat_session(request):
    if request.user.is_authenticated:
        try:
            latest_session = ChatSession.objects.filter(user=request.user).latest('last_visited')
            return JsonResponse({'session_id': str(latest_session.id)})
        except ChatSession.DoesNotExist:
            return JsonResponse({'session_id': None})
    return JsonResponse({'session_id': None})

def start_chat(request):
    if request.user.is_authenticated:
        try:
            # Try to get the latest chat session
            latest_session = ChatSession.objects.filter(user=request.user).latest('last_visited')
            # Redirect to the latest session
            return redirect(f'/chat/{request.user.username}/{latest_session.id}/')
        except ChatSession.DoesNotExist:
            # If no chat sessions exist, create a new one with "Default Chat" as the name
            assistant, created = Assistant.objects.get_or_create(
                defaults={'name': 'Default Assistant', 'role': 'This is a default assistant.'}
            )
            session_id = generate_session_id()
            ChatSession.objects.create(
                id=session_id,
                user=request.user,
                assistant=assistant,
                title="Default Chat Created By System",
            )

            return redirect('chatting', session_id=session_id,username = request.user.username)
    return redirect('/login/')
@csrf_exempt
def chatting_messages(request, username, session_id):
    if request.method == 'GET':
        try:

            session = ChatSession.objects.get(id=session_id, user__username=username)

            chat_history = ChatHistory.objects.filter(session=session).order_by('timestamp')
            chat_history_list = [
                {
                    'user': request.user.username,
                    'content': message.message,
                    'timestamp': message.timestamp.isoformat(),
                    'number': message.number
                }
                for message in chat_history
            ]

            return JsonResponse({'status': 'success', 'chat_history': chat_history_list})

        except ChatSession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Chat session not found or access denied'}, status=404)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in chatting_messages view: {e}")
            return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
def chatting(request, username, session_id):
    try:

        session = get_object_or_404(ChatSession, id=session_id, user__username=username)

        chat_history = ChatHistory.objects.filter(session=session).order_by('timestamp')

    except ChatSession.DoesNotExist:
        return HttpResponse("Chat session not found or access denied", status=404)

    return render(request, 'prank/chatting.html', {
        'session': session,
        'chat_history': chat_history,
        'username': username,
    })

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.save()

            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('profile')

            messages.error(request, 'Authentication failed. Please try logging in.')
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'prank/signup.html', {'form': form})

@csrf_exempt
def handle_message(request, username, session_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'status': 'error', 'message': 'No message provided'}, status=400)

            if not request.user.is_authenticated or request.user.username != username:
                return JsonResponse({'status': 'error', 'message': 'User not authenticated or invalid user'}, status=401)

            user = request.user

            try:
                session = ChatSession.objects.get(id=session_id, user=user)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)

            ai_response = get_openai_response(user_message)

            ChatHistory.objects.create(
                session=session,
                number=ChatHistory.get_next_number(session),
                message=user_message
            )
            ChatHistory.objects.create(
                session=session,
                number=ChatHistory.get_next_number(session),
                message=ai_response
            )

            session.last_visited = timezone.now()
            session.save()

            return JsonResponse({'status': 'success', 'ai_response': ai_response})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
def chat_history(request, username):
    if request.user.username != username:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-last_visited').values('id', 'title')
    chat_sessions_list = list(chat_sessions)
    print(chat_sessions_list)
    return JsonResponse({'status': 'success', 'sessions': chat_sessions_list})

@csrf_exempt
def new_chat(request, username):
    user = request.user
    if user.is_authenticated:
        assistant, created = Assistant.objects.get_or_create(
            defaults={'name': 'Default Assistant', 'role': 'This is a default assistant.'}
        )
        data = json.loads(request.body)
        chat_name = data.get('title')
        if created:
            print("A new default assistant has been created.")

        if not assistant:
            return HttpResponse("Default assistant not available.", status=500)

        session_id = generate_session_id()
        ChatSession.objects.create(
            id=session_id,
            user=user,
            assistant=assistant,
            title=chat_name,
        )

        return redirect('chatting', session_id=session_id,username = request.user.username)

    else:
        return redirect('login')
@csrf_exempt
def delete_chat(request, username , session_id):
    user = request.user
    if user.is_authenticated:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.delete()
            messages.success(request, 'Chat session created successfully.')
            return redirect('new_chat')
        except ChatSession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Chat session not found or access denied'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            remember_me = request.POST.get('remember_me')
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'prank/login.html', {'form': form})

def profile(request):
    user = request.user
    chat_sessions = ChatSession.objects.filter(user=user).order_by('-last_visited')
    return render(request, 'prank/profile.html', {
        'user': user,
        'chat_sessions': chat_sessions,
    })

def logout_user(request):
    auth_logout(request)
    return redirect('home')

def export_chat_history(request):
    user = request.user
    session = ChatSession.objects.filter(user=user).order_by('-last_visited').first()
    if not session:
        return HttpResponse("No chat history available", status=404)

    chat_history = ChatHistory.objects.filter(session=session)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_chat_history.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Role', 'Message'])
    for chat in chat_history:
        writer.writerow([chat.timestamp, chat.role, chat.message])

    return response
