from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import APIView
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, \
    ChangeUserPasswordSerializer, HotelSerializer, \
    CustomBookSerializer, CustomBookViewSerializer, RoomsAvailableSerializer, RoomAddSerilizer, AllUserSerializer
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


class AllUserView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        users = User.objects.all()
        serializer = AllUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            user.delete()
            return Response({"message": "User Deleted Successfully"}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"Message": "user not exists"}, status=status.HTTP_400_BAD_REQUEST)


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


# class SendPasswordResetEmailView(APIView):
#
#     def post(self, request):
#         serializer = SendPasswordResetEmailSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         return Response({"message": "password reset mail sent"})


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


class RoomAddView(APIView):
    def post(self, request, pk):
        hotel_id = pk
        request.data['hotel_id'] = hotel_id
        serializer = RoomAddSerilizer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoomsAvailableView(APIView):
    def post(self, request, pk):
        check_in_str = request.data.get('check_in_date')
        check_out_str = request.data.get('check_out_date')

        if check_in_str:

            check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            if check_in_date < timezone.now().date() or check_out_date < timezone.now().date():
                return Response(
                    {"Message": "No time machines here! Booking is strictly for the present and future, not the past."},
                    status=status.HTTP_400_BAD_REQUEST)

            if check_out_date <= check_in_date:
                return Response({"message": "Check-out date should be greater than check-in date"},
                                status=status.HTTP_400_BAD_REQUEST)

            available_rooms = Room.objects.filter(
                hotel_id=pk,
            ).exclude(
                Q(booking__check_in_date__lte=check_out_date, booking__check_out_date__gte=check_in_date)
            ).distinct()
            print(available_rooms)
            serializer = RoomsAvailableSerializer(available_rooms, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Please enter all data"}, status=status.HTTP_400_BAD_REQUEST)


class CustomBookingView(APIView):
    # def get(self, request, pk):
    #     try:
    #         data = Room.objects.filter(hotel_id=pk)
    #         serializer = HotelRoomSerializer(data, many=True, context={'request': request})
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except ValueError:
    #         raise Response({"message": "Sorry no rooms available!"}, status=status.HTTP_306_RESERVED)

    def post(self, request, pk, pk2):

        room = Room.objects.get(id=pk2)
        print(room)

        try:
            check_in_str = request.data.get('check_in_date')
            check_out_str = request.data.get('check_out_date')
            if check_in_str:
                check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

                if check_out_date <= check_in_date:
                    return Response({"message": "Check-out date should be after check-in date"},
                                    status=status.HTTP_400_BAD_REQUEST)
                # print("---------")
                conflicting_bookings = Booking.objects.filter(
                    Q(room_id=pk2, check_in_date__lte=check_out_date, check_out_date__gte=check_in_date)
                )
                #                 print("----------Hello------")
                if conflicting_bookings.exists():
                    return Response({"message": "Room is not available for the requested dates"},
                                    status=status.HTTP_400_BAD_REQUEST)
                #                 print("------AFter conflict---")
                total_days = (check_out_date - check_in_date).days
                total_price = total_days * room.price_per_night
        #                 print("------AFter conflict---")
        except ValueError:
            return Response({"message": "Please enter all data"}, status=status.HTTP_400_BAD_REQUEST)
        #         print("------AFter conflict---")
        booking_data = {
            'room_id': pk2,
            'guest_name': request.data.get('guest_name', ''),
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'total_price': total_price
        }
        #         print("------AFter conflict---")
        serializer = CustomBookSerializer(data=booking_data)
        serializer.is_valid(raise_exception=True)
        #         print("------AFter conflict--------------------")
        room.is_available = False
        room.save()
        serializer.save()
        return Response({"message": "Room book Successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            booking = Booking.objects.get(id=pk)
            print(booking)
            booking.delete()
        except ObjectDoesNotExist:
            return Response({"message": "There is no booking for this room"}, status=status.HTTP_400_BAD_REQUEST)
        # room = Room.objects.get(id=pk2)

        # room.is_available = True
        # room.save()
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
            all = request.query_params.get('all')
            bookings = request.query_params.get('booking')
            today = request.query_params.get('today')
            print(all)
            if all:
                data = Room.objects.filter(hotel_id=pk)
                serializer = RoomAddSerilizer(data, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            if bookings:
                data = Booking.objects.filter(room_id__hotel_id=pk)
            if today:
                data = Booking.objects.filter(check_in_date=timezone.now().date())
            serializer = CustomBookViewSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            raise Response({"message": "Sorry no bookings available!"}, status=status.HTTP_306_RESERVED)
