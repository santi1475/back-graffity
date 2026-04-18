from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.core.exceptions import ValidationError


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    """Manager personalizado para User con email como identificador único."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    username = None  # Elimina el campo heredado de AbstractUser

    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_CHOICES = [
        (GENDER_MALE, 'Masculino'),
        (GENDER_FEMALE, 'Femenino'),
    ]

    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    type_document = models.CharField(max_length=20, null=True, blank=True)
    n_document = models.CharField(max_length=20, null=True, blank=True)
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} {self.surname or ''}".strip()


class Company(BaseModel):
    razon_social = models.CharField(max_length=255)
    razon_social_comercial = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    n_document = models.CharField(max_length=255, null=True, blank=True)  # RUC
    birth_date = models.DateField(null=True, blank=True)
    
    ubigeo_region = models.CharField(max_length=255, null=True, blank=True)
    ubigeo_provincia = models.CharField(max_length=255, null=True, blank=True)
    ubigeo_distrito = models.CharField(max_length=255, null=True, blank=True)
    
    region = models.CharField(max_length=255, null=True, blank=True)
    provincia = models.CharField(max_length=255, null=True, blank=True)
    distrito = models.CharField(max_length=255, null=True, blank=True)
    
    address = models.TextField(null=True, blank=True)
    urbanizacion = models.CharField(max_length=255, null=True, blank=True)
    cod_local = models.CharField(max_length=255, null=True, blank=True)

    def clean(self):
        # Aseguramos el patrón Singleton (sólo un registro de esta tabla)
        if self._state.adding and Company.objects.exists():
            raise ValidationError("Solo puede existir un registro de la pestaña Company (Singleton).")
        super().clean()

    def __str__(self):
        return self.razon_social


class Category(BaseModel):
    title = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='categories/', null=True, blank=True)
    icon_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Brand(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    image = models.ImageField(upload_to='brands/', null=True, blank=True)
    icon_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name='products')
    
    price_general = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_company = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(null=True, blank=True)
    
    is_discount = models.BooleanField(default=False)
    max_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    disponiblidad = models.IntegerField(default=1)
    
    state = models.SmallIntegerField(default=1)
    state_stock = models.SmallIntegerField(default=1)
    unidad_medida = models.CharField(max_length=50, null=True, blank=True)
    stock = models.IntegerField(default=0)
    
    include_igv = models.BooleanField(default=True)
    is_icbper = models.BooleanField(default=False)
    is_ivap = models.BooleanField(default=False)
    percentage_isc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_especial_nota = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['sku', 'barcode']),
        ]

    def __str__(self):
        return self.title
