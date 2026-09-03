from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations utilisateur
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'company_name', 'company_siret',
            'created_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour JWT avec informations utilisateur
    """
    
    def validate(self, attrs):
        # Authentification standard
        data = super().validate(attrs)
        
        # Ajouter les informations utilisateur au token
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'company_name': self.user.company_name,
            'dashboard_url': self.user.get_dashboard_url(),
        }
        
        return data

class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion utilisateur
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Chercher l'utilisateur par email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError('Aucun utilisateur trouvé avec cet email.')
            
            # Authentifier avec username
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('Ce compte est désactivé.')
                attrs['user'] = user
            else:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
        else:
            raise serializers.ValidationError('Email et mot de passe requis.')
        
        return attrs

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    # Champs optionnels pour les entreprises
    company_address = serializers.CharField(required=False, allow_blank=True)
    company_phone = serializers.CharField(required=False, allow_blank=True)
    siret = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone', 'address',
            'company_name', 'company_siret', 'company_address', 'company_phone', 'siret'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation spécifique pour les entreprises
        role = attrs.get('role')
        if role == 'ENTREPRISE':
            if not attrs.get('company_name'):
                raise serializers.ValidationError("Le nom de l'entreprise est requis pour les comptes entreprise.")
            if not attrs.get('siret'):
                raise serializers.ValidationError("Le numéro SIRET est requis pour les comptes entreprise.")
        
        # Seuls PARTICULIER et ENTREPRISE peuvent s'inscrire
        if role not in ['PARTICULIER', 'ENTREPRISE']:
            raise serializers.ValidationError("Seuls les particuliers et entreprises peuvent s'inscrire directement.")
        
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value
    
    def validate_siret(self, value):
        if value and len(value.replace(' ', '')) != 14:
            raise serializers.ValidationError("Le numéro SIRET doit contenir exactement 14 chiffres.")
        return value
    
    def create(self, validated_data):
        # Supprimer password_confirm des données
        validated_data.pop('password_confirm')
        
        # Gérer le champ SIRET (utiliser siret pour company_siret)
        siret = validated_data.pop('siret', None)
        if siret:
            validated_data['company_siret'] = siret
        
        # Créer l'utilisateur
        password = validated_data.pop('password')
        role = validated_data.get('role')
        
        # Les entreprises sont inactives par défaut, les particuliers sont actifs
        if role == 'ENTREPRISE':
            validated_data['is_active'] = False
        else:  # PARTICULIER
            validated_data['is_active'] = True
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur (lecture/modification)
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'company_name', 'company_siret',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'role', 'created_at', 'updated_at']