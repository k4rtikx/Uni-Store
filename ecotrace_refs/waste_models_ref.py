from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
import uuid

class FormulaireCollecte(models.Model):
    """
    Modèle pour les formulaires de collecte soumis par les particuliers/entreprises
    """
    
    # Types de déchets
    TYPE_DECHETS_CHOICES = [
        ('ordinateur', 'Ordinateur / Laptop'),
        ('smartphone', 'Smartphone / Tablette'),
        ('electromenager', 'Électroménager'),
        ('televiseur', 'Téléviseur / Écran'),
        ('composants', 'Composants électroniques'),
        ('autres', 'Autres'),
    ]
    
    # Quantités estimées
    QUANTITE_CHOICES = [
        ('1-5kg', '1-5 kg'),
        ('5-10kg', '5-10 kg'),
        ('10-20kg', '10-20 kg'),
        ('20kg+', 'Plus de 20 kg'),
    ]
    
    # Créneaux horaires
    CRENEAU_CHOICES = [
        ('matin', 'Matin (8h-12h)'),
        ('apres_midi', 'Après-midi (14h-18h)'),
        ('flexible', 'Flexible'),
    ]
    
    # Mode de collecte
    MODE_COLLECTE_CHOICES = [
        ('domicile', 'Collecte à domicile - Vous attendez'),
        ('apport', 'Apport volontaire - Vous apportez'),
    ]
    
    # Statuts du formulaire
    STATUT_CHOICES = [
        ('SOUMIS', 'Soumis'),
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
        ('EN_COURS', 'En cours de traitement'),
        ('TERMINE', 'Terminé'),
    ]
    
    # Champs principaux
    reference = models.CharField(
        max_length=20, 
        unique=True, 
        default='', 
        help_text='Référence unique du formulaire'
    )
    
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='formulaires_collecte'
    )
    
    # Informations sur les déchets
    type_dechets = models.CharField(
        max_length=20,
        choices=TYPE_DECHETS_CHOICES,
        help_text='Type de déchets à collecter'
    )
    
    description = models.TextField(
        help_text='Description détaillée des déchets'
    )
    
    quantite_estimee = models.CharField(
        max_length=10,
        choices=QUANTITE_CHOICES,
        blank=True,
        null=True,
        help_text='Quantité estimée'
    )
    
    # Mode de collecte
    mode_collecte = models.CharField(
        max_length=20,
        choices=MODE_COLLECTE_CHOICES,
        default='domicile',
        help_text='Mode de collecte choisi'
    )
    
    # Informations de planification
    date_souhaitee = models.DateField(
        help_text='Date souhaitée pour la collecte'
    )
    
    creneau_horaire = models.CharField(
        max_length=15,
        choices=CRENEAU_CHOICES,
        blank=True,
        null=True,
        help_text='Créneau horaire souhaité'
    )
    
    # Coordonnées
    adresse_collecte = models.TextField(
        blank=True,
        null=True,
        help_text='Adresse où effectuer la collecte (obligatoire pour collecte à domicile)'
    )
    
    telephone = models.CharField(
        max_length=20,
        help_text='Numéro de téléphone de contact'
    )
    
    instructions_speciales = models.TextField(
        blank=True,
        null=True,
        help_text='Instructions particulières pour la collecte'
    )
    
    # Photos
    photo1 = models.ImageField(
        upload_to='formulaires/photos/',
        blank=True,
        null=True,
        help_text='Photo des déchets (optionnel)'
    )
    
    photo2 = models.ImageField(
        upload_to='formulaires/photos/',
        blank=True,
        null=True,
        help_text='Photo supplémentaire (optionnel)'
    )
    
    photo3 = models.ImageField(
        upload_to='formulaires/photos/',
        blank=True,
        null=True,
        help_text='Photo supplémentaire (optionnel)'
    )
    
    # Statut et suivi
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='SOUMIS'
    )
    
    # Champs pour la gestion administrative
    urgence = models.CharField(
        max_length=20,
        choices=[
            ('faible', 'Faible'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
        ],
        default='normale',
        help_text='Niveau d\'urgence de la demande'
    )
    
    notes_admin = models.TextField(
        blank=True,
        null=True,
        help_text='Notes administratives'
    )
    
    motif_rejet = models.TextField(
        blank=True,
        null=True,
        help_text='Motif du rejet si applicable'
    )
    
    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='formulaires_valides',
        help_text='Administrateur qui a validé/rejeté'
    )
    
    date_validation = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Date de validation/rejet'
    )
    
    # Informations pour l'apport volontaire
    point_collecte = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Point de collecte pour apport volontaire'
    )
    
    horaires_ouverture = models.TextField(
        blank=True,
        null=True,
        help_text='Horaires d\'ouverture du point de collecte'
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_traitement = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'waste_formulaire_collecte'
        verbose_name = 'Formulaire de collecte'
        verbose_name_plural = 'Formulaires de collecte'
        ordering = ['-date_creation']
    
    def save(self, *args, **kwargs):
        # Générer une référence unique si elle n'existe pas
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)
    
    def generer_reference(self):
        """Générer une référence unique pour le formulaire avec gestion des conflits"""
        today = timezone.now()
        prefix = f"COL-{today.year}-"
        
        # Utiliser une transaction atomique pour éviter les race conditions
        with transaction.atomic():
            # Boucle avec retry pour gérer les conflits potentiels
            for attempt in range(50):  # Maximum 50 tentatives
                # Compter les formulaires créés aujourd'hui + tentatives
                count = FormulaireCollecte.objects.filter(
                    date_creation__date=today.date()
                ).count() + 1 + attempt
                
                reference = f"{prefix}{count:03d}"
                
                # Vérifier si la référence existe déjà
                if not FormulaireCollecte.objects.filter(reference=reference).exists():
                    return reference
            
            # Si toutes les tentatives échouent, utiliser un UUID pour garantir l'unicité
            unique_suffix = uuid.uuid4().hex[:6].upper()
            return f"{prefix}{unique_suffix}"
    
    def valider(self, validateur=None):
        """Valider le formulaire et créer une collecte si nécessaire"""
        self.statut = 'VALIDE'
        self.date_traitement = timezone.now()
        
        # Créer une collecte automatiquement si mode domicile
        if self.mode_collecte == 'domicile':
            collecte = Collecte.objects.create(
                utilisateur=self.utilisateur,
                formulaire_origine=self,
                date_collecte=self.date_souhaitee,
                date_prevue=self.date_souhaitee,
                mode_collecte='domicile',
                adresse=self.adresse_collecte,
                telephone=self.telephone,
                statut='PLANIFIEE'
            )
        
        self.save()
        return True
    
    def rejeter(self, raison=""):
        """Rejeter le formulaire"""
        self.statut = 'REJETE'
        self.date_traitement = timezone.now()
        self.instructions_speciales += f"\n\nRejeté: {raison}"
        self.save()
        return True
    
    def get_photos(self):
        """Retourner la liste des photos non vides"""
        photos = []
        for photo_field in [self.photo1, self.photo2, self.photo3]:
            if photo_field:
                photos.append(photo_field.url)
        return photos
    
    def get_collecte_associee(self):
        """Retourner la collecte associée à ce formulaire"""
        try:
            return self.collectes_associees.first()
        except:
            return None
    
    def __str__(self):
        return f"{self.reference} - {self.utilisateur.username} ({self.get_statut_display()})"

class Collecte(models.Model):
    """
    Modèle pour les collectes programmées
    """
    # Statuts basés sur le diagramme
    STATUT_CHOICES = [
        ('PLANIFIEE', 'Planifiée'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    # Mode de collecte
    MODE_COLLECTE_CHOICES = [
        ('domicile', 'Collecte à domicile'),
        ('apport', 'Apport volontaire'),
    ]
    
    # Champs principaux
    reference = models.CharField(
        max_length=20, 
        unique=True, 
        default='',
        help_text='Référence unique de la collecte'
    )
    
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collectes'
    )
    
    formulaire_origine = models.ForeignKey(
        FormulaireCollecte,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='collectes_associees',
        help_text='Formulaire à l\'origine de cette collecte'
    )
    
    # Dates
    date_collecte = models.DateField()
    date_prevue = models.DateField(null=True, blank=True)
    
    # Mode et statut
    mode_collecte = models.CharField(
        max_length=20,
        choices=MODE_COLLECTE_CHOICES,
        default='domicile'
    )
    
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='PLANIFIEE'
    )
    
    # Informations de collecte
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    
    # Transporteur assigné
    transporteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transports_assignes',
        limit_choices_to={'role': 'TRANSPORTEUR'}
    )
    
    # Point de collecte (pour apport volontaire)
    point_collecte = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'waste_collecte'
        verbose_name = 'Collecte'
        verbose_name_plural = 'Collectes'
        ordering = ['-date_collecte']
    
    def save(self, *args, **kwargs):
        # Générer une référence unique si elle n'existe pas
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)
    
    def generer_reference(self):
        """Générer une référence unique pour la collecte avec gestion des conflits"""
        today = timezone.now()
        prefix = f"RDV-{today.year}-"
        
        # Utiliser une transaction atomique pour éviter les race conditions
        with transaction.atomic():
            # Boucle avec retry pour gérer les conflits potentiels
            for attempt in range(50):  # Maximum 50 tentatives
                # Compter les collectes créées aujourd'hui + tentatives
                count = Collecte.objects.filter(
                    created_at__date=today.date()
                ).count() + 1 + attempt
                
                reference = f"{prefix}{count:03d}"
                
                # Vérifier si la référence existe déjà
                if not Collecte.objects.filter(reference=reference).exists():
                    return reference
            
            # Si toutes les tentatives échouent, utiliser un UUID pour garantir l'unicité
            unique_suffix = uuid.uuid4().hex[:6].upper()
            return f"{prefix}{unique_suffix}"
    
    def mettre_a_jour_statut(self, nouveau_statut):
        """Mettre à jour le statut de la collecte"""
        if nouveau_statut in dict(self.STATUT_CHOICES):
            self.statut = nouveau_statut
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.reference} - {self.utilisateur.username} ({self.date_collecte})"

class Dechet(models.Model):
    """
    Modèle pour les déchets collectés
    """
    # États de traitement
    ETAT_CHOICES = [
        ('COLLECTE', 'Collecté'),
        ('TRI', 'En cours de tri'),
        ('A_RECYCLER', 'À recycler'),
        ('RECYCLE', 'Recyclé'),
        ('A_DETRUIRE', 'À détruire'),
        ('DETRUIT', 'Détruit'),
    ]
    
    # Informations du déchet
    type = models.CharField(max_length=100, help_text='Type de déchet électronique')
    categorie = models.CharField(max_length=100, help_text='Catégorie du déchet')
    description = models.TextField(blank=True, null=True)
    quantite = models.FloatField(help_text='Quantité en kg')
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='COLLECTE')
    
    # Relations
    collecte = models.ForeignKey(
        Collecte,
        on_delete=models.CASCADE,
        related_name='dechets'
    )
    
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dechets_traites',
        limit_choices_to={'role': 'TECHNICIEN'}
    )
    
    # Photos du déchet
    photo_avant = models.ImageField(
        upload_to='dechets/photos/',
        blank=True,
        null=True,
        help_text='Photo avant traitement'
    )
    
    photo_apres = models.ImageField(
        upload_to='dechets/photos/',
        blank=True,
        null=True,
        help_text='Photo après traitement'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'waste_dechet'
        verbose_name = 'Déchet'
        verbose_name_plural = 'Déchets'
        ordering = ['-created_at']
    
    def valoriser(self, technicien, nouvel_etat):
        """Valoriser le déchet (traitement par un technicien)"""
        self.technicien = technicien
        self.etat = nouvel_etat
        self.date_traitement = timezone.now()
        self.save()
        return True
    
    def __str__(self):
        return f"{self.type} - {self.quantite}kg ({self.get_etat_display()})"