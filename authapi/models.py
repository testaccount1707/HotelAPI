from django.utils import timezone

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from rest_framework.exceptions import ValidationError


# Validators
# def rating_validator(value):
#     if value > 5 or value < 1:
#         raise ValidationError("Review Between 0 to 5")
#     else:
#         return value


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, name, tc, password=None, password2=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            tc=tc,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, tc, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
            tc=tc,
        )
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 1)

        if extra_fields.get('role') != 1:
            raise ValueError('Superuser must have role of Global Admin')

        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email",
        max_length=255,
        unique=True,
    )

    name = models.CharField(max_length=200)
    tc = models.BooleanField()
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    crated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['name', 'tc']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        # "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        # "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Hotel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=10)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    email = models.EmailField()

    def __str__(self):
        return self.name


class Room(models.Model):
    hotel_id = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room_no = models.IntegerField()
    room_type = models.CharField(max_length=255, choices=(
        ('Standard Room', 'Standard Room'), ('Deluxe Room', 'Deluxe Room'), ('Suite', 'Suite'),
        ('Executive Suite', 'Executive Suite'), ('Poolside Room', 'Poolside Room')))
    price_per_night = models.IntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hotel_id.name}, {self.room_no}, {self.id}"


class Booking(models.Model):
    room_id = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=255)
    check_in_date = models.DateField(validators=[MinValueValidator(limit_value=timezone.now().date())])
    check_out_date = models.DateField(validators=[MinValueValidator(limit_value=timezone.now().date())])
    total_price = models.IntegerField()

    def clean(self):
        if self.check_out_date < self.check_in_date:
            raise ValidationError("Check-out date cannot be before check-in date.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.guest_name} - {self.room_id.room_no} - {self.check_in_date} to {self.check_out_date}"


class Review(models.Model):
    hotel_id = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    date_posted = models.DateField(auto_now_add=True)
