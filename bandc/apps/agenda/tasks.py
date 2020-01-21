from .models import BandC, Document


def pull(bandc_pk: int):
    band = BandC.objects.get(pk=bandc_pk)
    band.pull()
