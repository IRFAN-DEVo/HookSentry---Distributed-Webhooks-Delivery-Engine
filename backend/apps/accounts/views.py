from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        from apps.workspaces.models import WorkspaceMember
        membership = WorkspaceMember.objects.filter(user=user).select_related('workspace').first()

        return Response({
            'user': UserSerializer(user).data,
            'workspace': {
                'id': str(membership.workspace.id),
                'name': membership.workspace.name,
                'slug': membership.workspace.slug,
                'role': membership.role,
            } if membership else None,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        from apps.workspaces.models import WorkspaceMember
        membership = WorkspaceMember.objects.filter(user=user).select_related('workspace').first()

        return Response({
            'user': UserSerializer(user).data,
            'workspace': {
                'id': str(membership.workspace.id),
                'name': membership.workspace.name,
                'slug': membership.workspace.slug,
                'role': membership.role,
            } if membership else None,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)

class MeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.workspaces.models import WorkspaceMember
        memberships = WorkspaceMember.objects.filter(user=request.user).select_related('workspace')
        workspaces_data = [
            {
                'id': str(m.workspace.id),
                'name': m.workspace.name,
                'slug': m.workspace.slug,
                'role': m.role,
            }
            for m in memberships
        ]

        return Response({
            'user': UserSerializer(request.user).data,
            'workspaces': workspaces_data,
        })

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Stateles JWT logout acknowledgment
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
