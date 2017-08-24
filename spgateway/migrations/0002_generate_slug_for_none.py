from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from spgateway.models import generate_slug


def generate_slug_for_none(apps, schema_editor):
    order_appname = settings.SPGATEWAY_ORDERMODEL.split('.', maxsplit=1)[0]
    order_classname = settings.SPGATEWAY_ORDERMODEL.split('.', maxsplit=1)[1]
    Order = apps.get_model(order_appname, order_classname)
    for each in Order.objects.filter(SpgatewaySlug=None):
        if not each.SpgatewaySlug:
            each.SpgatewaySlug = generate_slug()
            each.save()


class Migration(migrations.Migration):
    dependencies = [
        ('spgateway', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(generate_slug_for_none),
    ]
