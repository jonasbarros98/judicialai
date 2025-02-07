# Generated by Django 5.1.1 on 2024-09-22 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0007_documentojuridico_dados_requerente_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentojuridico',
            name='anexo',
            field=models.FileField(blank=True, null=True, upload_to='anexos/', verbose_name='Anexo'),
        ),
        migrations.AddField(
            model_name='documentojuridico',
            name='provas',
            field=models.TextField(blank=True, null=True, verbose_name='Provas'),
        ),
        migrations.AlterField(
            model_name='documentojuridico',
            name='dados_requerente',
            field=models.TextField(blank=True, null=True, verbose_name='Dados do Requerente'),
        ),
        migrations.AlterField(
            model_name='documentojuridico',
            name='dados_requerido',
            field=models.TextField(blank=True, null=True, verbose_name='Dados do Requerido'),
        ),
    ]
