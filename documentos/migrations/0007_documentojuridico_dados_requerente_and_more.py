# Generated by Django 5.1.1 on 2024-09-22 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0006_remove_ementajuridica_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentojuridico',
            name='dados_requerente',
            field=models.TextField(default='', verbose_name='Dados do Requerente'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='documentojuridico',
            name='dados_requerido',
            field=models.TextField(default='', verbose_name='Dados do Requerido'),
            preserve_default=False,
        ),
    ]
