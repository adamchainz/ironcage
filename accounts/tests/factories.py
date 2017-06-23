from accounts.models import User


def create_user(name='Alice', **kwargs):
    email_addr = f'{name.lower()}@example.com'
    return User.objects.create_user(email_addr=email_addr, name=name, **kwargs)


def create_user_with_full_profile(name='Alice'):
    kwargs = {
        'year_of_birth': 1985,
        'gender': 'Female',
        'ethnicity': 'Mixed',
        'nationality': 'British',
        'country_of_residence': 'United Kingdom',
        'dont_ask_demographics': False,
        'accessibility_reqs_yn': False,
        'accessibility_reqs': None,
        'childcare_reqs_yn': False,
        'childcare_reqs': None,
        'dietary_reqs_yn': True,
        'dietary_reqs': 'Vegan',
    }
    return create_user(name, **kwargs)


def create_user_with_dont_ask_demographics_set(name='Alice', **kwargs):
    return create_user(name, dont_ask_demographics=True, **kwargs)