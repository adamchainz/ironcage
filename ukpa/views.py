from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


from .forms import NominationForm
from .models import Nomination


def new_nomination(request):
    if request.user.is_authenticated and request.user.get_nomination():
        messages.warning(request, 'You have already submitted a nomination')
        return redirect(request.user.get_nomination())

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        form = NominationForm(request.POST)
        if form.is_valid():
            nomination = form.save(commit=False)
            nomination.nominee = request.user
            nomination.save()
            messages.success(request, 'Thank you for submitting your nomination')
            slack_message('ukpa/nomination_created.slack', {'nomination': nomination})
            return redirect(nomination)
    else:
        form = NominationForm()

    context = {
        'form': form,
    }
    return render(request, 'ukpa/new_nomination.html', context)


@login_required
def nomination_edit(request, nomination_id):
    nomination = Nomination.objects.get_by_nomination_id_or_404(nomination_id)

    if request.user != nomination.nominee:
        messages.warning(request, 'Only the nominee can update the nomination')
        return redirect('index')

    if request.method == 'POST':
        form = NominationForm(request.POST, instance=nomination)
        if form.is_valid():
            nomination = form.save()
            nomination.save()
            messages.success(request, 'Thank you for updating your nomination')
            return redirect(nomination)
    else:
        form = NominationForm(instance=nomination)

    context = {
        'form': form,
    }
    return render(request, 'ukpa/nomination_edit.html', context)


@login_required
def nomination(request, nomination_id):
    nomination = Nomination.objects.get_by_nomination_id_or_404(nomination_id)

    if request.user != nomination.nominee:
        messages.warning(request, 'Only the nominee can view the nomination')
        return redirect('index')

    context = {
        'nomination': nomination,
        'form': NominationForm(),
    }
    return render(request, 'ukpa/nomination.html', context)


@login_required
@require_POST
def nomination_delete(request, nomination_id):
    nomination = Nomination.objects.get_by_nomination_id_or_404(nomination_id)

    if request.user == nomination.nominee:
        nomination.delete()
        messages.success(request, 'Your nomination has been withdrawn')
    else:
        messages.warning(request, 'Only the nominee can withdraw the nomination')

    return redirect('index')
