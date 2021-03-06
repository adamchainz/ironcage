import json
import os

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.shortcuts import get_object_or_404

from accommodation.models import Booking
from grants.models import Application
from ironcage.utils import Scrambler
from tickets.models import Ticket
from ukpa.models import Nomination

from .managers import UserManager


# https://en.wikipedia.org/wiki/Member_states_of_the_United_Nations
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'countries.txt')) as f:
    COUNTRIES = [line.strip() for line in f]

# https://en.wikipedia.org/wiki/List_of_adjectival_and_demonymic_forms_for_countries_and_nations
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'nationalities.txt')) as f:
    NATIONALITIES = [line.strip() for line in f]

# https://www.ons.gov.uk/ons/guide-method/harmonisation/primary-set-of-harmonised-concepts-and-questions/ethnic-group.pdf
with open(os.path.join(settings.BASE_DIR, 'accounts', 'data', 'ethnicities.json')) as f:
    ETHNICITIES = json.load(f)


class Manager(UserManager):
    def get_by_user_id_or_404(self, user_id):
        id = self.model.id_scrambler.backward(user_id)
        return get_object_or_404(self.model, pk=id)


class User(AbstractBaseUser, PermissionsMixin):
    YEAR_OF_BIRTH_CHOICES = [['not shared', 'prefer not to say']] + [[str(year), str(year)] for year in range(1917, 2017)]

    GENDER_CHOICES = [
        ['not shared', 'prefer not to say'],
        ['female', 'female'],
        ['male', 'male'],
        ['other', 'please specify'],
    ]

    COUNTRY_CHOICES = [['not shared', 'prefer not to say']] + [[country, country] for country in COUNTRIES] + [['other', 'not listed here (please specify)']]

    NATIONALITY_CHOICES = [['not shared', 'prefer not to say']] + [[nationality, nationality] for nationality in NATIONALITIES] + [['other', 'not listed here (please specify)']]

    # Sorry
    ETHNICITY_CHOICES = [['not shared', 'prefer not to say']] + [[ethnicity_category, [[ethnicity, ethnicity] for ethnicity in ethnicities]] for ethnicity_category, ethnicities in ETHNICITIES]

    email_addr = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'That email address has already been registered',
        },
    )
    name = models.CharField(max_length=200)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    year_of_birth = models.CharField(max_length=10, null=True, blank=True, choices=YEAR_OF_BIRTH_CHOICES)
    gender = models.CharField(max_length=100, null=True, blank=True, choices=GENDER_CHOICES)
    ethnicity = models.CharField(max_length=100, null=True, blank=True, choices=ETHNICITY_CHOICES)
    ethnicity_free_text = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True, choices=NATIONALITY_CHOICES)
    country_of_residence = models.CharField(max_length=100, null=True, blank=True, choices=COUNTRY_CHOICES)
    dont_ask_demographics = models.BooleanField(default=False)
    accessibility_reqs_yn = models.NullBooleanField()
    accessibility_reqs = models.TextField(null=True, blank=True)
    childcare_reqs_yn = models.NullBooleanField()
    childcare_reqs = models.TextField(null=True, blank=True)
    dietary_reqs_yn = models.NullBooleanField()
    dietary_reqs = models.TextField(null=True, blank=True)
    is_ukpa_member = models.NullBooleanField(null=True, blank=True)
    has_booked_hotel = models.NullBooleanField()
    volunteer_setup = models.NullBooleanField()
    volunteer_session_chair = models.NullBooleanField()
    volunteer_videoer = models.NullBooleanField()
    volunteer_reg_desk = models.NullBooleanField()
    is_contributor = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email_addr'
    EMAIL_FIELD = 'email_addr'
    REQUIRED_FIELDS = ['name']

    id_scrambler = Scrambler(8000)

    objects = Manager()

    @property
    def user_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_full_name(self):
        '''This is used by the admin.'''
        return self.name

    def get_short_name(self):
        '''This is used by the admin.'''
        return self.name

    def get_ticket(self):
        try:
            return self.ticket
        except Ticket.DoesNotExist:
            return None

    def get_accommodation_booking(self):
        try:
            return self.booking
        except Booking.DoesNotExist:
            return None

    def get_grant_application(self):
        try:
            return self.grant_application
        except Application.DoesNotExist:
            return None

    def get_nomination(self):
        try:
            return self.nomination
        except Nomination.DoesNotExist:
            return None

    def profile_complete(self):
        if any(v is None for v in [
            self.accessibility_reqs_yn,
            self.childcare_reqs_yn,
            self.dietary_reqs_yn,
        ]):
            return False

        if self.get_ticket() is not None and self.is_ukpa_member is None:
            return False

        if self.dont_ask_demographics:
            return True

        return all(v for v in [
            self.year_of_birth,
            self.gender,
            self.ethnicity,
            self.nationality,
            self.country_of_residence
        ])

    def submitted_single_proposal(self):
        return len(self.proposals.all()) == 1

    def accepted_proposals(self):
        return [p for p in self.proposals.all() if p.is_accepted()]

    def rejected_proposals(self):
        return [p for p in self.proposals.all() if p.is_rejected()]

    def all_proposals_accepted(self):
        return len(self.proposals.all()) > 0 and len(self.proposals.all()) == len(self.accepted_proposals())

    def any_proposals_accepted(self):
        return len(self.accepted_proposals()) > 0

    def some_proposals_accepted(self):
        return self.any_proposals_accepted() and not self.all_proposals_accepted()

    def one_proposal_rejected(self):
        return len(self.rejected_proposals()) == 1

    def one_proposal_accepted(self):
        return len(self.accepted_proposals()) == 1

    def things_volunteered_for(self):
        things = []
        if self.volunteer_setup:
            things.append('Help with setup at 6am on Thursday morning')
        if self.volunteer_session_chair:
            things.append('Chair a session')
        if self.volunteer_videoer:
            things.append('Help with videoing talks')
        if self.volunteer_reg_desk:
            things.append('Staff the registration desk')
        return things

    def get_free_dinner_booking(self):
        if not self.is_contributor:
            return None

        return self.dinner_bookings.filter(stripe_charge_id=None).first()

    def get_contributors_dinner_booking(self):
        return self.dinner_bookings.filter(venue='contributors').first()

    def get_conference_dinner_booking(self):
        return self.dinner_bookings.filter(venue='conference').first()
