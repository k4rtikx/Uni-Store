from .models import Notification
from waste_management.models import FormulaireCollecte, Collecte, Dechet
from users.models import User
from django.utils import timezone
from django.db import models
from datetime import timedelta

class NotificationService:
    """
    Service pour créer des notifications intelligentes basées sur les événements
    """
    
    @staticmethod
    def create_notification(title, message, notification_type='info', category='system', 
                          priority='normal', user=None, target_role=None, action_url=None,
                          object_type=None, object_id=None, expires_in_days=30):
        """
        Créer une nouvelle notification
        """
        expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
        
        notification = Notification.objects.create(
            title=title,
            message=message,
            type=notification_type,
            category=category,
            priority=priority,
            user=user,
            target_role=target_role,
            action_url=action_url,
            object_type=object_type,
            object_id=object_id,
            expires_at=expires_at
        )
        
        return notification
    
    @staticmethod
    def notify_new_formulaire(formulaire):
        """
        Notifier les administrateurs d'un nouveau formulaire
        """
        NotificationService.create_notification(
            title="Nouveau formulaire de collecte",
            message=f"Un nouveau formulaire {formulaire.reference} a été soumis par {formulaire.utilisateur.username}",
            notification_type='info',
            category='demande',
            priority='normal',
            target_role='ADMINISTRATEUR',
            action_url=f'/dashboard/administrateur?section=demandes&formulaire={formulaire.id}',
            object_type='formulaire',
            object_id=formulaire.id
        )
    
    @staticmethod
    def notify_formulaire_validated(formulaire):
        """
        Notifier l'utilisateur que son formulaire a été validé
        """
        NotificationService.create_notification(
            title="Formulaire validé",
            message=f"Votre demande de collecte {formulaire.reference} a été approuvée",
            notification_type='success',
            category='demande',
            priority='normal',
            user=formulaire.utilisateur,
            action_url=f'/dashboard/{formulaire.utilisateur.role.lower()}?section=formulaires'
        )
        
        # Notifier les responsables logistiques pour planification
        NotificationService.create_notification(
            title="Nouvelle demande à planifier",
            message=f"Le formulaire {formulaire.reference} a été validé et doit être planifié",
            notification_type='warning',
            category='planification',
            priority='high',
            target_role='RESPONSABLE_LOGISTIQUE',
            action_url=f'/dashboard/responsable-logistique?section=planification',
            object_type='formulaire',
            object_id=formulaire.id
        )
    
    @staticmethod
    def notify_collecte_assigned(collecte):
        """
        Notifier le transporteur d'une nouvelle collecte assignée
        """
        if collecte.transporteur:
            NotificationService.create_notification(
                title="Nouvelle collecte assignée",
                message=f"La collecte {collecte.reference} vous a été assignée pour le {collecte.date_collecte.strftime('%d/%m/%Y')}",
                notification_type='info',
                category='collecte',
                priority='high',
                user=collecte.transporteur,
                action_url=f'/dashboard/transporteur?section=collectes',
                object_type='collecte',
                object_id=collecte.id
            )
    
    @staticmethod
    def notify_collecte_completed(collecte):
        """
        Notifier la fin d'une collecte
        """
        # Notifier le client
        if collecte.formulaire_origine:
            NotificationService.create_notification(
                title="Collecte terminée",
                message=f"Votre collecte {collecte.reference} a été effectuée avec succès",
                notification_type='success',
                category='collecte',
                priority='normal',
                user=collecte.formulaire_origine.utilisateur,
                action_url=f'/dashboard/{collecte.formulaire_origine.utilisateur.role.lower()}?section=collectes'
            )
        
        # Notifier les techniciens des nouveaux déchets
        dechets_count = collecte.dechets.count()
        if dechets_count > 0:
            NotificationService.create_notification(
                title="Nouveaux déchets à traiter",
                message=f"{dechets_count} nouveaux déchets de la collecte {collecte.reference} nécessitent un traitement",
                notification_type='info',
                category='valorisation',
                priority='normal',
                target_role='TECHNICIEN',
                action_url='/dashboard/technicien?section=dechets'
            )
    
    @staticmethod
    def get_role_notifications(user_role, user_id=None, unread_only=False):
        """
        Récupérer les notifications pour un rôle spécifique
        """
        query = Notification.objects.filter(
            models.Q(target_role=user_role) | 
            (models.Q(user_id=user_id) if user_id else models.Q(user_id__isnull=True))
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
        
        if unread_only:
            query = query.filter(read=False)
        
        return query.order_by('-created_at')