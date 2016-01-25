import factory

from .models import BandC


class BandCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BandC
