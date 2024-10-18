from django.contrib.auth.models import User
from django.db import models
from pydantic import ValidationError

class DocumentoJuridico(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('peticao_inicial', 'Petição Inicial'),
        ('contestacao', 'Contestação'),
         ('apelacao', 'Apelação'),
    ]
    
    tipo = models.CharField(
        max_length=50, 
        choices=TIPO_DOCUMENTO_CHOICES, 
        verbose_name='Tipo de Documento',
        default='peticao_inicial'  # Valor padrão definido
    )
    
    titulo = models.CharField(
        max_length=255, 
        verbose_name='Título do Documento'
    )
    
    conteudo = models.TextField(
        verbose_name='Conteúdo do Documento'
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Data de Criação'
    )

    # Relacionamento com o usuário (obrigatório)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')

    # Campos adicionais
    tipo_acao = models.CharField(
        max_length=255, 
        verbose_name='Tipo de Ação'
    )
    
    valor_causa = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Valor da Causa'
    )
    
    juizo_competente = models.CharField(
        max_length=255, 
        verbose_name='Juízo Competente'
    )
    
    descricao_fatos = models.TextField(
        verbose_name='Descrição dos Fatos',
        blank=True,  # Torna o campo opcional
        null=True
    )
    
    dados_requerente = models.TextField(
        verbose_name='Dados do Requerente',
        blank=True,  # Torna o campo opcional
        null=True
    )
    
    dados_requerido = models.TextField(
        verbose_name='Dados do Requerido',
        blank=True,  # Torna o campo opcional
        null=True
    )

    # Novo campo para armazenar as provas
    provas = models.TextField(
        verbose_name='Provas',
        blank=True,  # Campo opcional
        null=True
    )

    # Campo para anexar um arquivo PDF da petição inicial
    anexo = models.FileField(
        upload_to='anexos/',  # Define o diretório para salvar os arquivos
        verbose_name='Anexo',
        blank=True,  # Campo opcional
        null=True
    )
    fundamentacao_fatos = models.TextField(
        verbose_name='Fundamentação dos Fatos',
        blank=True,  # Campo opcional,
        null=True
    )
    
    fundamentacao_direito = models.TextField(
        verbose_name='Fundamentação do Direito',
        blank=True,  # Campo opcional
        null=True
    )
    
    processo_numero = models.CharField(
        max_length=255, 
        verbose_name='Número do Processo',
        blank=True,  # Campo opcional
        null=True
    )
    
    justica_gratis = models.BooleanField(
        default=False,
        verbose_name='Adicionar pedido de justiça grátis'
    )
    
    class Meta:
        verbose_name = 'Documento Jurídico'
        verbose_name_plural = 'Documentos Jurídicos'
        ordering = ['-data_criacao']  # Documentos mais recentes primeiro
    
    def __str__(self):
        return f"{self.titulo} - {self.tipo} ({self.data_criacao.strftime('%Y-%m-%d')})"
    
    # Validação personalizada para valor_causa
    def clean(self):
        if self.valor_causa <= 0:
            raise ValidationError('O valor da causa deve ser maior que zero.')
        


class EmentaJuridica(models.Model):
    numero_processo = models.CharField(max_length=50)
    orgao_julgador = models.CharField(max_length=255, null=True, blank=True)
    ministro_relator = models.CharField(max_length=255, null=True, blank=True)
    data_julgamento = models.DateField(null=True, blank=True)
    data_publicacao = models.DateField(null=True, blank=True)
    tipo_documento = models.CharField(max_length=50, null=True, blank=True)
    referencias_legais = models.TextField(null=True, blank=True)
    ementa = models.TextField()
    palavras_chave = models.TextField(null=True, blank=True)
    fonte = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.numero_processo
    
    class Meta:
        db_table = 'documentos_ementajuridica'
