# Generated by Django 5.1.1 on 2024-09-23 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0010_documentojuridico_fundamentacao_direito_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentojuridico',
            name='descricao_fatos',
            field=models.TextField(blank=True, null=True, verbose_name='Descrição dos Fatos'),
        ),
    ]
