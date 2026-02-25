from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    name = models.CharField(max_length=100, blank=True)
    gmail = models.EmailField(unique=True)
    phonenumber = models.CharField(max_length=15)

    def __str__(self):
        return self.username

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return self.name


class Student(models.Model):
    BRANCH_CHOICES = [
        ("CS", "CS"),
        ("IS", "IS"),
        ("EC", "EC"),
        ("ME", "ME"),
    ]

    name = models.CharField(max_length=120)
    usn = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=5, choices=BRANCH_CHOICES)
    sem = models.PositiveSmallIntegerField(default=1)
    sec = models.CharField(max_length=2, default="A")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.usn})"


class Teacher(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    subject = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    class_section = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "date", "subject", "class_section")
        ordering = ["-date", "student__name"]

    def __str__(self):
        return f"{self.student.usn} - {self.date} - {'Present' if self.is_present else 'Absent'}"
