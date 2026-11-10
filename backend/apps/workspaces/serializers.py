import uuid
from rest_framework import serializers
from django.utils.text import slugify
from .models import Workspace, WorkspaceMember, APIKey
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer

class WorkspaceSerializer(serializers.ModelSerializer):
    current_user_role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at', 'current_user_role', 'member_count']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'current_user_role', 'member_count']

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        member = obj.memberships.filter(user=request.user).first()
        return member.role if member else None

    def get_member_count(self, obj):
        return obj.memberships.count()

    def create(self, validated_data):
        user = self.context['request'].user
        name = validated_data['name']
        slug_base = slugify(name) or 'workspace'
        slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"
        workspace = Workspace.objects.create(name=name, slug=slug)

        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceMember.Role.OWNER
        )

        from apps.audit.models import AuditLog
        AuditLog.log_action(
            workspace=workspace,
            actor=user,
            action=AuditLog.Action.WORKSPACE_CREATED,
            details={'workspace_id': str(workspace.id), 'name': workspace.name}
        )

        return workspace

class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'user_email', 'role', 'joined_at']
        read_only_fields = ['id', 'workspace', 'user', 'joined_at']

    def create(self, validated_data):
        user_email = validated_data.pop('user_email', None)
        workspace = validated_data['workspace']
        if not user_email:
            raise serializers.ValidationError({"user_email": "User email is required."})

        try:
            target_user = User.objects.get(email=user_email.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_email": f"No user registered with email {user_email}."})

        if WorkspaceMember.objects.filter(workspace=workspace, user=target_user).exists():
            raise serializers.ValidationError({"user_email": "User is already a member of this workspace."})

        member = WorkspaceMember.objects.create(
            workspace=workspace,
            user=target_user,
            role=validated_data.get('role', WorkspaceMember.Role.MEMBER)
        )

        from apps.audit.models import AuditLog
        AuditLog.log_action(
            workspace=workspace,
            actor=self.context['request'].user,
            action=AuditLog.Action.MEMBER_ADDED,
            details={'added_user_id': str(target_user.id), 'added_user_email': target_user.email, 'role': member.role}
        )
        return member

class APIKeySerializer(serializers.ModelSerializer):
    raw_key = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = ['id', 'workspace', 'name', 'prefix', 'raw_key', 'is_active', 'created_at', 'expires_at', 'last_used_at']
        read_only_fields = ['id', 'workspace', 'prefix', 'created_at', 'last_used_at']

class CreateAPIKeySerializer(serializers.ModelSerializer):
    raw_key = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = ['id', 'name', 'expires_at', 'raw_key']
        read_only_fields = ['id', 'raw_key']

    def create(self, validated_data):
        workspace = self.context['workspace']
        actor = self.context['request'].user
        instance, raw_key = APIKey.generate_key(
            workspace=workspace,
            name=validated_data['name'],
            expires_at=validated_data.get('expires_at')
        )
        instance.raw_key = raw_key

        from apps.audit.models import AuditLog
        AuditLog.log_action(
            workspace=workspace,
            actor=actor,
            action=AuditLog.Action.API_KEY_CREATED,
            details={'api_key_id': str(instance.id), 'name': instance.name, 'prefix': instance.prefix}
        )
        return instance
