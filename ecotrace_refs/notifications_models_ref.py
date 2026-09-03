from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    Modèle pour les notifications spécifiques aux rôles
    """
    
    # Types de notifications
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('urgent', 'Urgent'),
    ]
    
    # Catégories de notifications
    CATEGORY_CHOICES = [
        ('collecte', 'Collecte'),
        ('demande', 'Demande'),
        ('utilisateur', 'Utilisateur'),
        ('system', 'Système'),
        ('valorisation', 'Valorisation'),
        ('planification', 'Planification'),
        ('validation', 'Validation'),
    ]
    
    # Priorités
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    
    # Champs principaux
    title = models.CharField(max_length=200, help_text='Titre de la notification')
    message = models.TextField(help_text='Contenu de la notification')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Destinataires
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text='Utilisateur destinataire (si null, notification globale pour le rôle)'
    )
    
    target_role = models.CharField(
        max_length=30,
        choices=[
            ('ADMINISTRATEUR', 'Administrateur'),
            ('TRANSPORTEUR', 'Transporteur'),
            ('TECHNICIEN', 'Technicien'),
            ('ENTREPRISE', 'Entreprise'),
            ('PARTICULIER', 'Particulier'),
            ('RESPONSABLE_LOGISTIQUE', 'Responsable Logistique'),
        ],
        null=True,
        blank=True,
        help_text='Rôle cible pour notification globale'
    )
    
    # État de la notification
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Action liée
    action_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text='URL vers l\'action à effectuer'
    )
    
    # Référence à un objet lié
    object_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Type d\'objet lié (formulaire, collecte, etc.)'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID de l\'objet lié'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date d\'expiration de la notification'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['target_role', 'read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        target = self.user.username if self.user else f"Role: {self.target_role}"
        return f"{self.title} - {target}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.read = True
        self.read_at = timezone.now()
        self.save()
    
    def is_expired(self):
        """Vérifier si la notification a expiré"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
