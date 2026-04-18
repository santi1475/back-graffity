from rest_framework import serializers
from .models import User, Company, Category, Brand, Product
from django.conf import settings
from django.contrib.auth.models import Group, Permission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename'] 

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permissions_pluck = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'created_at', 'permissions', 'permissions_pluck']

    def get_permissions_pluck(self, obj):
        return obj.permissions.values_list('codename', flat=True)

    def get_created_at(self, obj):
        return "2024/01/01 12:00 AM"

class UserSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(source='role', read_only=True)
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    # Usamos el created_at de tu BaseModel
    created_at = serializers.DateTimeField(format="%Y-%m-%d %I:%M %p", read_only=True)
    gender_text = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'name', 'surname', 'email', 'role_id', 'role', 
            'phone', 'avatar', 'type_document', 'n_document', 
            'gender', 'gender_text', 'is_active', 'created_at'
        ]

    def get_role(self, obj):
        if obj.role:
            return {"id": obj.role.id, "name": obj.role.name}
        return None

    def get_avatar(self, obj):
        if obj.avatar:
            return f"{settings.MEDIA_URL}{obj.avatar}"
        return None

class BrandSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['id', 'name', 'image', 'icon_name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'image', 'created_at', 'updated_at']

    def get_image(self, obj):
        if obj.image:
            return f"{settings.MEDIA_URL}{obj.image}"
        return None
    
class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'title', 'image', 
            'icon_name', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'image', 'created_at']

    def get_image(self, obj):
        if obj.imagen:
            return f"{settings.MEDIA_URL}{obj.imagen}"
        return None
    
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    
    class Meta:
        model = Product
        exclude = ['is_deleted', 'updated_at']