import os
import yaml
import re
import shutil
from yaml import SafeLoader
from datetime import datetime
import streamlit as st
from models import session, Contrato, Obra, Foto
from sqlalchemy import func

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

def sanitizar_caminho_pasta(caminho_pasta):
    """
    Sanitiza o caminho da pasta, substituindo caracteres não permitidos.

    :param caminho_pasta: String, caminho da pasta a ser sanitizado.
    :return: String, caminho sanitizado.
    """
    # Define os caracteres que você deseja substituir
    caracteres_invalidos = r'[<>:"/\\|?*]'  # Adicione mais caracteres se necessário

    # Substitui caracteres inválidos por um caractere permitido (por exemplo, '-')
    caminho_sanitizado = re.sub(caracteres_invalidos, '-', caminho_pasta)

    return caminho_sanitizado

def verificar_ou_criar_pasta(caminho_pasta):
    """
    Verifica se a pasta existe; caso não exista, cria a pasta no caminho especificado.

    :param caminho_pasta: String, caminho completo da pasta que deseja verificar/criar
    """
    # caminho_pasta = sanitizar_caminho_pasta(caminho_pasta)
    try:
        if not os.path.exists(caminho_pasta):
            os.makedirs(caminho_pasta)
            return True
    except Exception as e:
        st.error(f"Erro ao criar a pasta: {e}")
        return False

def salvar_fotos_na_pasta(contrato, obra, diario, arquivos):

    '''
        Salva os arquivos fornecidos na pasta correspondente, troca o nome dele para
        o ano o mes e o dia, acrescente a a palavra 'diario', o id do diario, a palavra 'arquivo' e o número de arquivos que 
        estão gravados pra aquele diário. 
        Exemplo: 2024.05.04_diario_7_arquivo_2.jpg
        7 é o número do diario
        2 é o terceiro arquivo cadastrado para aquela entrada do diário

        :param contrato: Objeto de Contrato, contrato ao qual o(s) arquivo(s) se refere(m)
        :param obra: Objeto de Obra, obra ao qual o(s) arquivo(s) se refere(m)
        :param diario: Objeto de Diario, diario ao qual o(s) arquivo(s) se refere(m)
        :param arquivos: Objeto, arquivos fornecidos no formulário de registro do diário como foram upados
        :return: Lista de String, o caminho completo de cada arquivo fornecido para registro no bd
    '''
    caminho_arquivos = []

    '''Consulta no banco de dados se já existem arquivos cadastrados para a entrada do,
    caso existam retorna a qtde de registros encontrados, caso não existam retorna 0
    '''
    contagem_fotos = session.query(func.count(Foto.id)).filter(Foto.diario_id == diario.id).scalar()

    # Verifica se existe uma pasta do contrato para salvar os arquivos, se não existir cria uma

    caminho_pasta_contrato = os.path.join(config['pasta_fotos'], contrato.nome)
    
    verificar_ou_criar_pasta(caminho_pasta_contrato)
    
    # Verifica se existe uma pasta da obra dentro da pasta do contrato para salvar os arquivos, se não existir cria uma
    caminho_pasta_obra = os.path.join(caminho_pasta_contrato, obra.nome)

    verificar_ou_criar_pasta(caminho_pasta_obra)
    
    # Verifica se existe uma pasta do diário, dentro da pasta da obra, dentro da pasta do contrato para salvar os arquivos, se não existir cria uma

    caminho_pasta_diario = os.path.join(caminho_pasta_obra, f"{diario.data.year}.{diario.data.month:02}.{diario.data.day:02}")

    verificar_ou_criar_pasta(caminho_pasta_diario)
    
    # Inicia o processo de salvamento dos arquivos dentro da pasta do diario

    for index, arquivo in enumerate(arquivos):
        extensao = os.path.splitext(arquivo.name)[1]  # Obtém a extensão do arquivo, incluindo o ponto
        '''O nome do arquivo usa o número de resultados para somar à qtde de arquivos que já existem 
        para impedir que seja sobreescritos'''
        nome_arquivo = f"{diario.data.year}.{diario.data.month:02}.{diario.data.day:02}_contrato_{sanitizar_caminho_pasta(contrato.numero)}_obra_{obra.id}_diario_{diario.id}_arquivo_{index + contagem_fotos + 1}{extensao}"
        caminho_destino = os.path.join(caminho_pasta_diario, nome_arquivo)
        
        try:
            with open(caminho_destino, "wb") as f:
                f.write(arquivo.getbuffer() if hasattr(arquivo, 'getbuffer') else arquivo.read())
            caminho_arquivos.append(caminho_destino)
        except Exception as e:
                print(f"Erro ao salvar o arquivo {arquivo}: {e}")
    return caminho_arquivos

@st.dialog("Apagar Foto")
def apagar_foto(foto):
    '''Remove a foto fornecida, apagando primeiro o arquivo e depois o registro do banco de dados
    
    :param foto: Objeto Foto, objeto instanciado de Foto, contendo os dados da foto escolhida
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''

    st.warning("Deseja mesmo apagar esta foto? Essa ação não poderá ser desfeita")
    st.image(foto.caminho_arquivo, width=400)
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            if os.path.exists(foto.caminho_arquivo):
                os.remove(foto.caminho_arquivo)
            session.delete(foto)
            session.commit()
            st.success("Foto apagada com sucesso")
            sleep(1)
            st.rerun()


# def backup_bd():

#     caminho_banco_dados = 'registro_obras.sqlite'
#     pasta_backup_google_drive = config['pasta_backup']
#     # Cria um nome de backup com data e hora
#     data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
#     nome_backup = f"backup_{data_hora}.sqlite"
#     caminho_backup = os.path.join(pasta_backup_google_drive, nome_backup)

#     try:
#         # Copia o banco de dados para a pasta de backup
#         shutil.copy(caminho_banco_dados, caminho_backup)
#         st.toast(f"Backup criado com sucesso")
#     except Exception as e:
#         st.toast(f"Erro ao criar backup: {e}")