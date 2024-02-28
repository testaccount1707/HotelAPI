from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import authenticate
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import APIView
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, \
    ChangeUserPasswordSerializer, SendPasswordResetEmailSerializer, UserResetPasswordSerializer, HotelSerializer, \
    HotelRoomSerializer, CustomBookSerializer, CustomBookViewSerializer
from .models import User, Hotel, Room, Booking
from rest_framework_simplejwt.tokens import RefreshToken


# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({'token': token, "message": "registration successfull"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.data.get('email')
            password = serializer.data.get('password')
            user = authenticate(email=email, password=password)

            if user is not None:
                token = get_tokens_for_user(user)
                return Response({'token': token, "message": "Login success"}, status=status.HTTP_200_OK)
            else:
                return Response({'errors': {"non_field_errors": ["Email password not valid"]}},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeUserPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangeUserPasswordSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid(raise_exception=True):
            return Response({"message": "password change successfull"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendPasswordResetEmailView(APIView):

    def post(self, request):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "password reset mail sent"})


class UserResetPasswordView(APIView):

    def post(self, request, uid, token):
        serializer = UserResetPasswordSerializer(data=request.data, context={'uid': uid, 'token': token})
        serializer.is_valid(raise_exception=True)
        return Response({"message": "password reset successfully"})


class HotelView(APIView):
    def get(self, request):
        data = Hotel.objects.all()
        rating = request.query_params.get('rating')
        search_hname = request.query_params.get('name')
        search_city = request.query_params.get('city')
        search_add = request.query_params.get('add')
        ordering = request.query_params.get('ordering')
        if search_hname:
            data = Hotel.objects.filter(name__icontains=search_hname)
        if search_city:
            data = Hotel.objects.filter(city__icontains=search_city)
        if search_add:
            data = Hotel.objects.filter(address__icontains=search_add)
        if rating:
            data = Hotel.objects.filter(rating=rating)
        if ordering:
            ordering_fields = ordering.split(",")
            data = data.order_by(*ordering_fields)
        serializer = HotelSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = HotelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SingleHotelView(APIView):
    def get(self, request, pk):
        data = Hotel.objects.get(pk=pk)
        serializer = HotelSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        data = Hotel.objects.get(pk=pk)
        serializer = HotelSerializer(instance=data, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        print(pk)
        try:
            instance = Hotel.objects.get(pk=pk)
            print(instance)
            instance.delete()
            return Response({"message": "Successfully Deleted!"}, status=status.HTTP_202_ACCEPTED)
        except Hotel.DoesNotExists:
            return Response({"message": "Data Does not Exists!"}, status=status.HTTP_404_NOT_FOUND)


class CustomView(APIView):
    def get(self, request, pk):
        try:
            data = Room.objects.filter(hotel_id=pk, is_available=True)
            serializer = HotelRoomSerializer(data, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            raise Response({"message": "Sorry no rooms available!"}, status=status.HTTP_306_RESERVED)

    def post(self, request, pk, pk2):

        room = Room.objects.get(id=pk2)
        print(room)

        try:
            check_in_date = request.data.get('check_in_date')
            check_out_date = request.data.get('check_out_date')
            if check_in_date:
                check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d')
                check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d')
                diff = (check_out_date - check_in_date).days
                print(diff)
                total_price = diff * room.price_per_night
                print(total_price)
                request.data['total_price'] = total_price
        except ValueError:
            return Response({"message": "Please enter all data"}, status=status.HTTP_400_BAD_REQUEST)

        request.data['room_id'] = pk2
        # if room.is_available == False:
        #     return Response({"message": "Room book Successfully"}, status=status.HTTP_400_BAD_REQUEST)
        # room.is_available = False
        # room.save()
        serializer = CustomBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if room.is_available == False:
            return Response({"message": "Room is already boook!"}, status=status.HTTP_400_BAD_REQUEST)
        room.is_available = False
        room.save()
        serializer.save()
        return Response({"message": "Room book Successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, pk, pk2):
        try:
            booking = Booking.objects.get(room_id=pk2)
            print(booking)
        except ObjectDoesNotExist:
            return Response({"message": "There is no booking for this room"}, status=status.HTTP_400_BAD_REQUEST)
        room = Room.objects.get(id=pk2)

        if booking is None:
            return Response({"message": "There is no booking"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            booking.delete()

        room.is_available = True
        room.save()
        return Response({"message": "Room booking canceled successfully"}, status=status.HTTP_200_OK)


# class HotelRoomView(APIView):
#
#     def get(self, request, pk):
#         try:
#             data = Room.objects.filter(hotel_id=pk, is_available=True)
#             serializer = HotelRoomSerializer(data, many=True, context={'request': request})
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except ValueError:
#             raise Response({"message": "Sorry no rooms available!"}, status=status.HTTP_306_RESERVED)
#
#     def post(self, request, pk):
#         room = Room.objects.get(room_no=request.data.get('room_id'))
#         request.data['room_id']
#         serialized_data = BookingSerializer(data=request.data)
#         print(request.data)
#         print(type(request.data['room_no']))
#
#         if serialized_data.is_valid(raise_exception=True):
#
#             print(room)
#             room.is_available = False
#             room.save()
#             print("---")
#             booking = serialized_data.save(room_id=room)
#             print(serialized_data.errors)
#             return Response({"message": "Room booked successfully!", "booking_id": booking.id},
#                             status=status.HTTP_200_OK)
#         else:
#             print(serialized_data.errors)
#             return Response(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomsBookingView(APIView):
    def get(self, request, pk):
        try:
            data = Booking.objects.filter(room_id__hotel_id=pk)
            serializer = CustomBookViewSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            raise Response({"message": "Sorry no bookings available!"}, status=status.HTTP_306_RESERVED)
