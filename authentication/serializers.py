from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'picture_url', 'birthday', 'email',
            'website', 'bio',
        ]
        read_only_fields = ['id']


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=3, max_length=100)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'birthday']

    def validate_username(self, value):
        if len(value) < 3 or len(value) > 50:
            raise serializers.ValidationError('Username must be between 3 and 50 characters.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserFbSignupSerializer(serializers.ModelSerializer):
    facebook_id = serializers.IntegerField()

    class Meta:
        model = User
        fields = [
            'username', 'email', 'birthday', 'facebook_id',
            'picture_url', 'first_name', 'last_name',
        ]

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.save()
        return user


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'website', 'bio']


class FacebookLoginSerializer(serializers.Serializer):
    facebook_token = serializers.CharField()


class ForgottenPasswordSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    password = serializers.CharField(min_length=3)
    confirm_password = serializers.CharField(min_length=3)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError('Passwords do not match.')
        return data
