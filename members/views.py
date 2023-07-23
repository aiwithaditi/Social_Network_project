# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UserSerializer
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.pagination import PageNumberPagination
from .models import FriendRequest
from .serializers import FriendRequestSerializer


@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['GET'])
def get_all_users(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def search_users(request):
    if request.method == 'GET':
        search_query = request.GET.get('query', '')
        users = User.objects.filter(username__icontains=search_query) | User.objects.filter(email__icontains=search_query)
        
        # Check if the search query is an exact email match
        exact_email_match = User.objects.filter(email=search_query).first()

        if exact_email_match:
            serializer = UserSerializer(exact_email_match)
            return Response(serializer.data)
        # Use pagination to limit the number of records per page (e.g., 10 records per page)
        paginator = PageNumberPagination()
        paginator.page_size = 3
        paginated_users = paginator.paginate_queryset(users, request)
        
        serializer = UserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)


#Friendrequest views

@api_view(['POST'])
def send_friend_request(request):
    if request.method == 'POST':
        sender = request.user
        receiver_username = request.data.get('receiver_username')

        try:
            receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            return Response({"message": "Receiver user does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if sender == receiver:
            return Response({"message": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
            return Response({"message": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request = FriendRequest(sender=sender, receiver=receiver)
        friend_request.save()

        return Response({"message": "Friend request sent successfully."}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def accept_friend_request(request, request_id):
    if request.method == 'POST':
        try:
            friend_request = FriendRequest.objects.get(pk=request_id, receiver=request.user, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({"message": "Friend request not found or already processed."}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'accepted'
        friend_request.save()

        return Response({"message": "Friend request accepted successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reject_friend_request(request, request_id):
    if request.method == 'POST':
        try:
            friend_request = FriendRequest.objects.get(pk=request_id, receiver=request.user, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({"message": "Friend request not found or already processed."}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'rejected'
        friend_request.save()

        return Response({"message": "Friend request rejected successfully."}, status=status.HTTP_200_OK)
