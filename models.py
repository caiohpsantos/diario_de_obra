from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Criar o engine do banco de dados SQLite
engine = create_engine('sqlite:///registro_obras.db')

# Base para os modelos do SQLAlchemy
Base = declarative_base()

# Tabela Contrato
class Contrato(Base):
    __tablename__ = 'contratos'
    numero = Column(String(50), primary_key=True)          # Número único do contrato
    nome = Column(String(255), nullable=False)          # Nome do contrato
    cliente = Column(String(255), nullable=False)       # Nome do cliente

    # Relacionamento com Obras (uma relação contrato -> várias obras)
    obras = relationship('Obra', back_populates='contrato')

    def __str__(self):
        return f"Contrato {self.numero}: {self.nome}"  # Define o formato de exibição do contrato

# Tabela Obra
class Obra(Base):
    __tablename__ = 'obra'
    id = Column(Integer, primary_key=True)               # ID único da obra
    nome = Column(String(255), nullable=False)           # Nome da obra
    local = Column(String(255), nullable=False)          # Localização da obra
    prazo = Column(Date, nullable=False)                 # Prazo de conclusão da obra
    contrato_numero = Column(Integer, ForeignKey('contratos.numero'))  # Chave estrangeira para contrato

    # Relacionamento com o contrato (muitas obras -> um contrato)
    contrato = relationship('Contrato', back_populates='obras')

    # Relacionamento com Diarios (uma obra -> vários diários)
    diarios = relationship('Diario', back_populates='obra')

    def __str__(self):
        # Acessa o relacionamento diretamente, evitando a necessidade de uma nova consulta
        return f"Obra {self.nome} do contrato {self.contrato.nome if self.contrato else 'Sem contrato'}"
# Tabela Diário
class Diario(Base):
    __tablename__ = 'diario'
    id = Column(Integer, primary_key=True)               # ID único do diário
    data = Column(Date, nullable=False)                  # Data do registro
    clima_manha = Column(String(50), nullable=False)     # Clima da manhã
    clima_tarde = Column(String(50), nullable=False)     # Clima da tarde
    clima_noite = Column(String(50), nullable=False)     # Clima da noite
    obra_id = Column(Integer, ForeignKey('obra.id'))     # Chave estrangeira para obra

    # Relacionamento com Obra (muitos diários -> uma obra)
    obra = relationship('Obra', back_populates='diarios')

    # Relacionamento com Fotos (um diário -> várias fotos)
    fotos = relationship('Foto', back_populates='diario')

# Tabela Foto
class Foto(Base):
    __tablename__ = 'foto'
    id = Column(Integer, primary_key=True)               # ID único da foto
    caminho_arquivo = Column(String(255), nullable=False) # Caminho do arquivo da foto
    descricao = Column(String(255))                      # Descrição opcional da foto
    diario_id = Column(Integer, ForeignKey('diario.id')) # Chave estrangeira para diário

    # Relacionamento com Diário (muitas fotos -> um diário)
    diario = relationship('Diario', back_populates='fotos')

# Criar todas as tabelas no banco de dados
Base.metadata.create_all(engine)

# Criar uma sessão para interagir com o banco
Session = sessionmaker(bind=engine)
session = Session()

