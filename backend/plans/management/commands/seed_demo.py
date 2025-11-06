from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from plans.models import Trip, Day, Place
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Seed the database with 3 demo trips (each with 2 days and 1 place)'

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='Jiening Yang',
            defaults={'email': 'jieningy@andrew.cmu.edu'}
        )
        if created:
            user.set_unusable_password()
            user.save()

        today = timezone.now().date()
        created_ids = []

        for i in range(1, 4):
            trip = Trip.objects.create(
                user=user,
                name=f'Demo Trip {i}',
                destination_city=f'City {i}',
                start_date=today + datetime.timedelta(days=i),
                end_date=today + datetime.timedelta(days=i + 1),
            )

            # two days per trip
            day1 = Day.objects.create(trip=trip, date=trip.start_date, order=1)
            day2 = Day.objects.create(trip=trip, date=trip.end_date, order=2)

            # one place on day1
            Place.objects.create(
                day=day1,
                name=f'Sample Place {i}',
                category='sight',
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
                notes='Demo place for UI testing',
                order=1,
                latitude=0.0,
                longitude=0.0,
                image_url='',
                address=''
            )

            created_ids.append(trip.id)

        self.stdout.write(self.style.SUCCESS(
            f'Created demo trips: {created_ids}'))
