from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec système de rôles pour EcoTrace
    """
    
    # Définition des rôles basés sur votre diagramme
    ROLE_CHOICES = [
        ('PARTICULIER', 'Particulier'),
        ('ENTREPRISE', 'Entreprise'),
        ('TRANSPORTEUR', 'Transporteur'),
        ('TECHNICIEN', 'Technicien'),
        ('ADMINISTRATEUR', 'Administrateur'),
        ('RESPONSABLE_LOGISTIQUE', 'Responsable Logistique'),
    ]
    
    # Champs supplémentaires
    role = models.CharField(
        max_length=25,
        choices=ROLE_CHOICES,
        default='PARTICULIER',
        help_text='Rôle de l\'utilisateur dans le système'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Numéro de téléphone'
    )
    
    address = models.TextField(
        blank=True,
        null=True,
        help_text='Adresse complète'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Pour les entreprises
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Nom de l\'entreprise (si applicable)'
    )
    
    company_siret = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        help_text='Numéro SIRET (si entreprise)'
    )
    
    company_address = models.TextField(
        blank=True,
        null=True,
        help_text='Adresse de l\'entreprise (si applicable)'
    )
    
    company_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Téléphone de l\'entreprise (si applicable)'
    )
    
    # Statut actif
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        if self.company_name:
            return f"{self.get_role_display()} - {self.company_name}"
        return f"{self.get_role_display()} - {self.get_full_name() or self.username}"
    
    @property
    def is_particulier(self):
        return self.role == 'PARTICULIER'
    
    @property
    def is_entreprise(self):
        return self.role == 'ENTREPRISE'
    
    @property
    def is_transporteur(self):
        return self.role == 'TRANSPORTEUR'
    
    @property
    def is_technicien(self):
        return self.role == 'TECHNICIEN'
    
    @property
    def is_administrateur(self):
        return self.role == 'ADMINISTRATEUR'
        
    @property
    def is_responsable_logistique(self):
        return self.role == 'RESPONSABLE_LOGISTIQUE'
    
    def can_access_dashboard(self, dashboard_type):
        """
        Vérifie si l'utilisateur peut accéder à un tableau de bord spécifique
        """
        return self.role.lower() == dashboard_type.lower()
    
    def get_dashboard_url(self):
        """
        Retourne l'URL du tableau de bord correspondant au rôle
        """
        dashboard_mapping = {
            'PARTICULIER': '/dashboard/particulier',
            'ENTREPRISE': '/dashboard/entreprise',
            'TRANSPORTEUR': '/dashboard/transporteur',
            'TECHNICIEN': '/dashboard/technicien',
            'ADMINISTRATEUR': '/dashboard/administrateur',
            'RESPONSABLE_LOGISTIQUE': '/dashboard/responsable-logistique',
        }
        return dashboard_mapping.get(self.role, '/dashboard')