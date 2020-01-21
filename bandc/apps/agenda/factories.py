import factory

from . import models


class BandCFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BandC


class MeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Meeting

    date = factory.Faker("date")
    bandc = factory.SubFactory(BandCFactory)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Document

    meeting = factory.SubFactory(MeetingFactory)
