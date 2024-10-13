# Generated by Django 5.1.1 on 2024-09-23 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0009_documentojuridico_processo_numero'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentojuridico',
            name='fundamentacao_direito',
            field=models.TextField(blank=True, null=True, verbose_name='Fundamentação do Direito'),
        ),
        migrations.AddField(
            model_name='documentojuridico',
            name='fundamentacao_fatos',
            field=models.TextField(blank=True, null=True, verbose_name='Fundamentação dos Fatos'),
        ),
    ]
