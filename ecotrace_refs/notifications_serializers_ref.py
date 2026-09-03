from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour les notifications
    """
    user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'type', 'category', 'priority',
            'user', 'target_role', 'read', 'read_at', 'action_url',
            'object_type', 'object_id', 'created_at', 'expires_at',
            'time_ago', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_time_ago(self, obj):
        """
        Calculer le temps écoulé depuis la création
        """
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    
    def get_is_expired(self, obj):
        """
        Vérifier si la notification a expiré
        """
        return obj.is_expired()

class CreateNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer des notifications
    """
    class Meta:
        model = Notification
        fields = [
            'title', 'message', 'type', 'category', 'priority',
            'user', 'target_role', 'action_url', 'object_type', 
            'object_id', 'expires_at'
        ]
    
    def validate(self, data):
        """
        Valider que soit user soit target_role est spécifié
        """
        if not data.get('user') and not data.get('target_role'):
            raise serializers.ValidationError(
                "Soit 'user' soit 'target_role' doit être spécifié"
            )
        return data