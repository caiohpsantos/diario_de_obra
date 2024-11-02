from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Criar o engine do banco de dados SQLite
engine = create_engine('sqlite:///registro_obras.sqlite')

# Base para os modelos do SQLAlchemy
Base = declarative_base()

# Tabela Contrato
class Contrato(Base):
    __tablename__ = 'contratos'
    numero = Column(String(50), primary_key=True)          # Número único do contrato
    nome = Column(String(255), nullable=False)          # Nome do contrato
    cliente = Column(String(255), nullable=False)       # Nome do cliente
    ativo = Column(Boolean, nullable=False)             # Marca se o contrato está ativo ou não

    # Relacionamento com Obras (uma relação contrato -> várias obras)
    obras = relationship('Obra', back_populates='contrato')

    def __str__(self):
        return f"{self.numero}: {self.nome}"  # Define o formato de exibição do contrato

# Tabela Obra
class Obra(Base):
    __tablename__ = 'obra'
    id = Column(Integer, primary_key=True)               # ID único da obra
    nome = Column(String(255), nullable=False)           # Nome da obra
    local = Column(String(255), nullable=False)          # Localização da obra
    inicio = Column(Date, nullable=False)                # Dia em que a obra começou
    termino = Column(Date, nullable=False)               # Prazo de conclusão da obra
    ativo = Column(Boolean, nullable=False)              # Marca se a obra ainda está ativa ou foi encerrada    
    contrato_numero = Column(Integer, ForeignKey('contratos.numero'))  # Chave estrangeira para contrato

    # Relacionamento com o contrato (muitas obras -> um contrato)
    contrato = relationship('Contrato', back_populates='obras')

    # Relacionamento com Diarios (uma obra -> vários diários)
    diarios = relationship('Diario', back_populates='obra')

    def __str__(self):
        # Acessa o relacionamento diretamente, evitando a necessidade de uma nova consulta
        return f"Obra {self.nome} do contrato {self.contrato.nome if self.contrato else 'Sem contrato'}"

# Tabela diario
class Diario(Base):
    __tablename__ = 'diario'
    id = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False)
    clima_manha = Column(String(50), nullable=True)
    clima_tarde = Column(String(50), nullable=True)
    clima_noite = Column(String(50), nullable=True)
    observacoes = Column(String(255), nullable=True)
    obra_id = Column(Integer, ForeignKey('obra.id'), nullable=False)

    # Relacionamento com Obra (muitos diários -> uma obra)
    obra = relationship('Obra', back_populates='diarios')

    # Relacionamento com Fotos (um diário -> várias fotos)
    fotos = relationship('Foto', back_populates='diario', cascade="all, delete-orphan")

    # Relacionamento com Servicos (um diário -> vários serviços)
    servicos = relationship('Servicos', back_populates='diario', cascade="all, delete-orphan")

    # Relacionamento com Efetivo Direto (um diário -> várias funções)
    efetivo_direto = relationship('Efetivo_Direto', back_populates='diario', cascade="all, delete-orphan")

    # Relacionamento com Efetivo Indireto (um diário -> várias funções)
    efetivo_indireto = relationship('Efetivo_Indireto', back_populates='diario', cascade="all, delete-orphan")

# Tabela Servicos
class Servicos(Base):
    __tablename__ = 'servicos'
    id = Column(Integer, primary_key=True)
    descricao = Column(String(255), nullable=False)
    item = Column(Integer, nullable=False)
    referencia = Column(String(255), nullable=False)
    diario_id = Column(Integer, ForeignKey('diario.id'))

    # Relacionamento com Diário (muitos servicos -> um diário)
    diario = relationship('Diario', back_populates='servicos')

# Tabela Efetivo Direto
class Efetivo_Direto(Base):
    __tablename__= 'efetivo_direto'
    id = Column(Integer, primary_key=True)
    funcao = Column(String(40), nullable=False)
    qtde = Column(Integer, nullable=False)
    presente = Column(Integer, nullable=False)
    diario_id = Column(Integer, ForeignKey('diario.id'))
    diario = relationship("Diario", back_populates="efetivo_direto")

# Tabela Efetivo Indireto
class Efetivo_Indireto(Base):
    __tablename__='efetivo_indireto'
    id = Column(Integer, primary_key=True)
    funcao = Column(String(40), nullable=False)
    efetivo = Column(Integer, nullable=False)
    diario_id = Column(Integer, ForeignKey('diario.id'))
    diario = relationship("Diario", back_populates="efetivo_indireto")

# Tabela Foto
class Foto(Base):
    __tablename__ = 'foto'
    id = Column(Integer, primary_key=True)               # ID único da foto
    caminho_arquivo = Column(String(255), nullable=False) # Caminho do arquivo da foto
    diario_id = Column(Integer, ForeignKey('diario.id')) # Chave estrangeira para diário

    # Relacionamento com Diário (muitas fotos -> um diário)
    diario = relationship('Diario', back_populates='fotos')

# Criar todas as tabelas no banco de dados
Base.metadata.create_all(engine)

# Criar uma sessão para interagir com o banco
Session = sessionmaker(bind=engine)
session = Session()



