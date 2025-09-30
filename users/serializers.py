from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import CustomUser, UserPreference
from notes.models import Note, Tag


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['theme', 'primary_color']


class UserSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'nickname',
            'age', 'gender', 'profile_image', 'preferences'
        ]
        read_only_fields = ['id']

    def validate_username(self, value):
        v = value.strip()
        if len(v) < 3:
            raise serializers.ValidationError('El username debe tener al menos 3 caracteres')
        qs = CustomUser.objects.filter(username__iexact=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este username ya está en uso')
        return v

    def validate_email(self, value):
        v = value.strip().lower()
        qs = CustomUser.objects.filter(email__iexact=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return v

    def update(self, instance, validated_data):
        remove_image = self.context['request'].data.get('remove_image')
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if remove_image == '1':
            instance.profile_image.delete(save=False)
            instance.profile_image = None
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Las contraseñas no coinciden'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    # Se mantiene el nombre 'username' para no romper el frontend, pero acepta username o email
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = (attrs.get('username') or '').strip()
        password = attrs.get('password')
        user = None

        # Intentar primero si es email
        if identifier and '@' in identifier:
            try:
                candidate = CustomUser.objects.get(email__iexact=identifier.lower())
                user = authenticate(username=candidate.username, password=password)
            except (CustomUser.DoesNotExist, CustomUser.MultipleObjectsReturned):
                user = None

        # Intentar como username normal si anterior falló
        if user is None:
            user = authenticate(username=identifier, password=password)

        if not user:
            raise serializers.ValidationError('Credenciales inválidas')
        attrs['user'] = user
        return attrs


class FlexibleTagsField(serializers.Field):
    def to_internal_value(self, data):
        # Aceptar lista o string
        if data in (None, ''):
            return []
        if isinstance(data, str):
            items = [t.strip() for t in data.split(',') if t.strip()]
        elif isinstance(data, list):
            items = []
            for t in data:
                if isinstance(t, str):
                    val = t.strip()
                    if val:
                        items.append(val)
                else:
                    raise serializers.ValidationError('Etiquetas deben ser cadenas')
        else:
            raise serializers.ValidationError('Formato de etiquetas inválido')
        return items

    def to_representation(self, value):
        # value es QuerySet o lista de Tag names ya manejado en to_representation principal
        return value


class NoteSerializer(serializers.ModelSerializer):
    tags = FlexibleTagsField(required=False)

    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'tags', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tags'] = [t.name for t in instance.tags.all()]
        return data

    def _save_tags(self, note, tags_list):
        if tags_list is None:
            return
        cleaned = []
        for raw in tags_list:
            name = raw.strip().lower()
            if not name:
                continue
            if len(name) > 40:
                name = name[:40]
            cleaned.append(name)
        unique = list(dict.fromkeys(cleaned))
        tag_objs = []
        for name in unique:
            tag, _ = Tag.objects.get_or_create(name=name)
            tag_objs.append(tag)
        note.tags.set(tag_objs)

    # validate_tags ya no necesario gracias al campo flexible

    def create(self, validated_data):
        tags_list = validated_data.pop('tags', [])
        # Si por algún motivo llega un string (fallback), convertir
        if isinstance(tags_list, str):
            tags_list = [t.strip() for t in tags_list.split(',') if t.strip()]
        note = Note.objects.create(**validated_data)
        self._save_tags(note, tags_list)
        return note

    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags', None)
        if isinstance(tags_list, str):
            tags_list = [t.strip() for t in tags_list.split(',') if t.strip()]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags_list is not None:
            self._save_tags(instance, tags_list)
        return instance