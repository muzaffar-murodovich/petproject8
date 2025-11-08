from shared.utility import check_email_or_phone, send_email, send_phone_code
from .models import (
                    User, UserConfirmation,
                    VIA_EMAIL, VIA_PHONE,
                    NEW, CODE_VERIFIED, DONE, PHOTO_STEP
                    )
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, exceptions
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail

class SignUpSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    

    class Meta:
        model = User
        fields = (
                  'id', 
                  'auth_type', 
                  'auth_status'
                  )
        
        extra_kwargs = {
            'auth_type': {'read_only': True, "required": False},
            'auth_status': {'read_only': True, "required": False},
        }
    
    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(verify_type=VIA_EMAIL)
            send_email(user.email, code)
        
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(verify_type=VIA_PHONE)
            send_email(user.phone_number, code)
            # send_phone_code(user.phone_number, code)
        
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data


    @staticmethod
    def auth_validate(data):
        print(data)
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        print("input_type:", input_type)
        print("user_input:", user_input)
        if input_type == 'email':
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL,
            }
        elif input_type == 'phone':
            data = {
                "phone_number": user_input,
                "auth_type": VIA_PHONE,
            }
        else:
            data = {
                "success": False,
                "message": "Email or phone number is required."
            }
            raise ValidationError(data)
        print(data)       
        
        return data



    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            data = {
                "success": False,
                "message": "A user with this email already exists."
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone_number=value).exists():
            data = {
                "success": False,
                "message": "A user with this phone number already exists."
            }
            raise ValidationError(data)

        return value
    
    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data

class ChangeUserInformation(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError(
                {
                    "message": "Passwords do not match."
                }
            )
        if password:
            validate_password(password)
            validate_password(confirm_password)
        
        return data
    
    def validate_username(self, username):
        if len(username) < 5 or len(username) > 35:
            raise ValidationError(
                {
                    "message": "Username must be at least 5 or at most 32 characters long."
                }
            )
        if username.isdigit():
            raise ValidationError(
                {
                    "message": "Username cannot be entirely numeric."
                }
            )
        return username
    
    def validate_first_name(self, first_name):
        if len(first_name) < 2 or len(first_name) > 30:
            raise ValidationError(
                {
                    "message": "First name must be at least 2 or at most 30 characters long."
                }
            )
        return first_name
    
    def validate_last_name(self, last_name):
        if len(last_name) < 2 or len(last_name) > 30:
            raise ValidationError(
                {
                    "message": "Last name must be at least 2 or at most 30 characters long."
                }
            )
        return last_name
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.password = validated_data.get('password', instance.password)
        instance.username = validated_data.get('username', instance.username)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()
        
        return instance