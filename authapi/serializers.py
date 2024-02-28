from rest_framework.exceptions import ValidationError

from .models import User
from rest_framework import serializers
from .models import User, Hotel, Booking, Review, Room
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password2', 'tc']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        password = attrs['password'],
        password2 = attrs['password2'],
        if password != password2:
            raise serializers.ValidationError("password and confirm password not match")
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=200)

    class Meta:
        model = User
        fields = ['email', 'password']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']


class ChangeUserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={"input_type": 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ['password', 'password2']

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs['password2']
        user = self.context.get('user')
        if password != password2:
            raise serializers.ValidationError("password and confirmpassword should be equal!")
        user.set_password(password)
        user.save()
        return attrs


class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        email = attrs['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            print("UID: ", uid)
            token = PasswordResetTokenGenerator().make_token(user)
            print("TOKEN: ", token)
            link = 'http://localhost:3000/api/reset/' + uid + '/' + token
            print("LINK: ", link)

            # Send email
            return attrs
        else:
            raise ValidationError('you are not existing user')


class UserResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={"input_type": 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ['password', 'password2']

        def validate(self, attrs):
            try:
                password = attrs['password']
                password2 = attrs['password2']
                uid = self.context.get('uid')
                token = self.context.get('token')

                if password != password2:
                    raise serializers.ValidationError("password and confirmPassword should be equal!")
                id = smart_str(urlsafe_base64_decode(uid))
                user = User.objects.get(id=id)
                if not PasswordResetTokenGenerator().check_token(user, token):
                    raise ValidationError("token is not valid or expired!")
                user.set_password(password)
                user.save()
                return attrs
            except DjangoUnicodeDecodeError:
                PasswordResetTokenGenerator().check_token(user, token)
                raise ValidationError("token is not valid or expired!")


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'address', 'city', 'contact_no', 'rating', 'email']


class CustomBookSerializer(serializers.ModelSerializer):
    total_price = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = ['room_id', 'guest_name', 'check_in_date', 'check_out_date', 'total_price']


class CustomBookViewSerializer(serializers.ModelSerializer):
    total_price = serializers.IntegerField()

    class Meta:
        model = Booking
        fields = ['room_id', 'guest_name', 'check_in_date', 'check_out_date', 'total_price']


# class BookingSerializer(serializers.ModelSerializer):
#     room_no = serializers.SerializerMethodField()
#     total_price = serializers.IntegerField(read_only=True)
#
#     class Meta:
#         model = Booking
#         fields = ['room_no', 'guest_name', 'check_in_date', 'check_out_date', 'total_price']
#
#     def get_room_no(self, obj):
#         return obj.room_id.room_no if obj.room_id else None
#
#     def create(self, validated_data):
#         room_no = validated_data.pop('room_no')
#
#         room = Room.objects.get(room_no=room_no)
#
#         check_in_date = validated_data.get('check_in_date')
#         check_out_date = validated_data.get('check_out_date')
#
#         diff = (check_out_date - check_in_date).days
#         total_price = diff * room.price_per_night
#         validated_data['total_price'] = total_price
#
#         booking = Booking.objects.create(room_no=room_no, **validated_data)
#         return booking


class HotelRoomSerializer(serializers.ModelSerializer):
    # we can use hyperlinkmodelserializer too with a required naming convention in the viwes url
    # hotel_name = serializers.SerializerMethodField()

    hotel_id = serializers.HyperlinkedRelatedField(
        queryset=Hotel.objects.all(),
        view_name='single-hotel',

    )

    class Meta:
        model = Room
        fields = ['id', 'hotel_id', 'room_no', 'room_type', 'price_per_night', 'is_available']

    # def get_hotel_name(self, obj):
    #     return obj.hotel_id.name if obj.hotel_id else None
