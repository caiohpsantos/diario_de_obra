import io
import os
import yaml
import re
import shutil
from PIL import Image
from fpdf import FPDF
from fpdf.fonts import FontFace
from time import sleep
from yaml import SafeLoader
from datetime import datetime
import streamlit as st
from models import session, Contrato, Obra, Foto, Efetivo_Direto, Efetivo_Indireto, Servicos
from sqlalchemy import func
from sqlalchemy.exc import PendingRollbackError


#Abre arquivo de configurações
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

#Funções que lidam com datas
def dia_da_semana(data):
    """
    Retorna o dia da semana correspondente a uma data.

    :param data: Uma string no formato 'DD/MM/AAAA'
    :return: Nome do dia da semana (em português)
    """
    dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
    
    # Retorna o nome do dia da semana correspondente
    return dias_semana[data.weekday()]

#Funções que lidam com a criação de pastas e gravação das fotos dos diários
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
        estão gravados pra aquele diário. Também redimensiona a imagem para um valor fixo, otimizado para o relatório em pdf. 
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
    sleep(0.5)
    # Verifica se existe uma pasta da obra dentro da pasta do contrato para salvar os arquivos, se não existir cria uma
    caminho_pasta_obra = os.path.join(caminho_pasta_contrato, obra.nome)

    verificar_ou_criar_pasta(caminho_pasta_obra)
    sleep(0.5)
    # Verifica se existe uma pasta do diário, dentro da pasta da obra, dentro da pasta do contrato para salvar os arquivos, se não existir cria uma

    caminho_pasta_diario = os.path.join(caminho_pasta_obra, f"{diario.data.year}.{diario.data.month:02}.{diario.data.day:02}")

    verificar_ou_criar_pasta(caminho_pasta_diario)
    sleep(0.5)
    # Inicia o processo de salvamento dos arquivos dentro da pasta do diario

    for index, arquivo in enumerate(arquivos):
        extensao = os.path.splitext(arquivo.name)[1]  # Obtém a extensão do arquivo, incluindo o ponto
        '''O nome do arquivo usa o número de resultados para somar à qtde de arquivos que já existem 
        para impedir que seja sobreescritos'''
        nome_arquivo = f"{diario.data.year}.{diario.data.month:02}.{diario.data.day:02}_contrato_{sanitizar_caminho_pasta(contrato.numero)}_obra_{obra.id}_diario_{diario.id}_arquivo_{index + contagem_fotos + 1}{extensao}"
        caminho_destino = os.path.join(caminho_pasta_diario, nome_arquivo)

        '''Redimensiona a imagem para um padrão fixo, otimizado para o relatório e salva usando o caminho_destino gerado'''
        
        try:
            imagem = Image.open(arquivo)
            imagem_redimensionada = imagem.resize((640,480))
            imagem_redimensionada.save(caminho_destino)  # Salva diretamente no destino
            caminho_arquivos.append(caminho_destino)
        except Exception as e:
                print(f"Erro ao salvar o arquivo {arquivo}: {e}")
    return caminho_arquivos

def apagar_fotos_na_pasta(caminho_arquivos):
    '''
    Apaga as fotos fornecidas na lista caminho_arquivos, apaga tbm as pastas criadas para armazená-las.

    :param caminho_arquivos: List, lista de caminhos de fotos
    :return: True caso consiga apagar as fotos e False caso haja algum problema, além de mensagem de erro.
    '''
    try:
        for arquivo in caminho_arquivos:
            if os.path.exists(arquivo):
                os.remove(arquivo)
                sleep(0.5)
    except FileNotFoundError:
        st.error(f"O arquivo {arquivo} não foi encontrado. É possível que haja problemas no armazenamento. Contate o suporte pelo formulário no canto direito: Report a Bug")
    except PermissionError:
        st.error(f"Permissão negada para apgar o arquivo {arquivo}. Contate o suporte pelo formulário de erros no menu no canto direito: Report a Bug.")
    except Exception as e:
        st.error(f"Houve um erro ao apagar a foto {caminho}. Contate o suporte pelo formulário no canto direito: Report a Bug")

#Funções que geram os modal (cxs de texto flutuante) para lidar com as remoções dos diários gravados (serviços, funções e fotos)
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

@st.dialog("Apagar Serviço")
def apagar_servico(servico):
    '''Remove o serviço fornecido, apagando o registro do banco de dados
    
    :param servico: Objeto Serviço, objeto instanciado de Serviço, contendo os dados do serviço escolhido
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''

    st.warning("Deseja mesmo apagar este serviço? Essa ação não poderá ser desfeita")
    st.write(f"Serviço: {servico.descricao} / Referência: {servico.referencia}")
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            session.delete(servico)
            session.commit()
            st.success("Serviço removido com sucesso")
            sleep(1)
            st.rerun()

@st.dialog("Apagar Função")
def apagar_funcao(funcao):
    '''Remove a função direta fornecida, apagando o registro do banco de dados
    
    :param funcao_direta: Objeto Funcao_Direta, objeto instanciado de Funcao_Direta, contendo os dados da função escolhida
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''

    st.warning("Deseja mesmo apagar esta função? Essa ação não poderá ser desfeita")
    st.write(funcao)
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            session.delete(funcao)
            session.commit()
            st.success("Função removida com sucesso")
            sleep(1)
            st.rerun()

@st.dialog("Apagar Obra")
def apagar_obra(obra):
    '''Remove a obra fornecida, apagando o registro do banco de dados
    
    :param obra: Objeto Obra, objeto instanciado de Obra, contendo os dados da obra escolhida
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''
    st.warning("Deseja mesmo apagar esta obra? Essa ação não poderá ser desfeita")
    st.write(obra)
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            session.delete(obra)
            session.commit()
            st.success("Obra removida com sucesso")
            sleep(1)
            st.rerun()

@st.dialog("Apagar Contrato")
def apagar_contrato(contrato):
    '''Remove o contrato fornecido, apagando o registro do banco de dados
    
    :param obra: Objeto Contrato, objeto instanciado de Contrato, contendo os dados do contrato escolhido
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''
    st.warning("Deseja mesmo apagar este contrato? Essa ação não poderá ser desfeita")
    st.write(contrato.nome)
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            session.delete(contrato)
            session.commit()
            st.success("Contrato removido com sucesso")
            sleep(1)
            st.rerun()

@st.dialog("Apagar Diário")
def apagar_diario(diario):
    '''Remove o diário fornecido, apagando o registro do banco de dados
    
    :param diário: Objeto Diário, objeto instanciado de Diário, contendo os dados do contrato escolhido
    :return: mensagem de aviso sobre ter ou não concluído o processo e finaliza a janela'''
    st.warning("Deseja mesmo apagar este diário? Essa ação não poderá ser desfeita. As fotos também serão apagadas.")
    st.write(diario)
    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Não"):
            st.error("Processo Cancelado")
            sleep(1)
            st.rerun()
    
    with col_apagar:
        if st.button("Sim"):
            with st.spinner():
                try:
                    for foto in session.query(Foto).filter_by(diario_id=diario.id).all():
                        apagar_fotos_na_pasta(foto.caminho_arquivo)
                    session.delete(diario)
                    session.commit()
                    st.success("Diário removido com sucesso.")
                    sleep(1)
                    st.rerun()
                except PendingRollbackError as e:
                    session.rollback()

#Funções que lidam com o relatório mensal

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pagina_inicial_cabecalho = 2  # Define a partir de qual página o cabeçalho aparece
        self.data = None
    
    # def header(self):
    #     # Exibe o cabeçalho somente a partir de uma página específica
    #     if self.page_no() >= self.pagina_inicial_cabecalho:
    #         self.set_font('helvetica', "B", 14)
    #         self.set_fill_color(255, 255, 255)
    #         self.cell(
    #         0, 0.7, f"RELATÓRIO FOTOGRÁFICO {self.data.strftime("%d/%m/%Y")}",
    #         fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT'
    #     )

    # def footer(self):
    #     # Position cursor at 1.5 cm from bottom:
    #     self.set_y(-2)
    #     # Setting font: helvetica italic 8
    #     self.set_font("helvetica", "B", 10)
    #     # Printing page number:
    #     self.cell(w=0, h=1, txt=f"Página {self.page_no()}", align="C")
    
    def desenhar_margens(self):
        # Define as bordas ao redor do documento
        margin = 1  # Tamanho da margem
        page_width = self.w - 2 * margin  # Largura da página sem margem
        page_height = self.h - 2 * margin  # Altura da página sem margem

        # Desenha um retângulo ao redor das bordas, com a espessura de linha desejada
        self.set_line_width(0.05)
        self.rect(margin, margin, page_width, page_height)

def gera_relatorios(diarios):
    
    pdf = PDF(unit="cm")
    
    #laço de repetição para criar as páginas de cada diário enviado
    for diario in diarios:

        pdf.data = diario.data

        pdf.add_page()
        #Cria as bordas do documento usando a função 
        pdf.desenhar_margens()
        
        #Insere a imagem da Rudra na página e depois cria a célula para rodeá-la
        pdf.image('images\\rudra.png',x=1.6, y=1.02, w=1, keep_aspect_ratio=True)
        pdf.set_font('helvetica', size=16)
        pdf.cell(2.5,1.3,border=True, new_x='LMARGIN')
        
        #Adiciona o título do relatório ao lado da célula da rudra
        pdf.cell(0,1.3,border=True, text="RELATÓRIO INTERNO DE ACOMPANHAMENTO DE OBRAS", align="R", new_x='LMARGIN', new_y='NEXT')
        
        #Muda o tamanho da fonte para 10 e põe em negrito, acrescenta um fundo cinza para a célula
        pdf.set_font('helvetica', "B", size=10)
        pdf.set_fill_color(200, 200, 200) #cor cinza para os enunciados
        #Cria a linha que especifica contrato/obra
        pdf.cell(3.16,0.5,"Obra: ", border=True, align="R",fill=True)
        pdf.multi_cell(15.84,0.5, f"{diario.obra.contrato.nome} - {diario.obra.nome}", new_x='LMARGIN', new_y='NEXT', border=True)

        #Cria a linha que especifica o cliente
        pdf.cell(3.16,0.5,"Cliente: ", border=True, align="R",fill=True)
        pdf.cell(15.84,0.5,diario.obra.contrato.cliente, new_x='LMARGIN', new_y='NEXT', border=True)

        #Cria a linha que especifica o local
        pdf.cell(3.16,0.5,"Local: ", border=True, align="R",fill=True)
        pdf.cell(15.84,0.5,diario.obra.local, new_x='LMARGIN', new_y='NEXT', border=True)

        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco para separação

        #Cria a linha que especifica início e término da obra
        pdf.cell(5.5,0.5,"Início da Obra: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(4,0.5,f"{diario.obra.inicio.strftime("%d/%m/%Y")}", border=True, align='C')
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(5.5,0.5,"Término da Obra: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(4,0.5,f"{diario.obra.termino.strftime("%d/%m/%Y")}", align='C', new_x='LMARGIN', new_y='NEXT', border=True)
        
        #Cria a linha que contabiliza os dias
        
        #Cria o Prazo da Obra
        prazo = (diario.obra.termino - diario.obra.inicio).days
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(3.16,0.7,"Prazo da Obra: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(3.16,0.7,f"{prazo} dias", border=True, align="C")
        
        #Cria o Tempo decorrido
        tempo_decorrido = (diario.data - diario.obra.inicio).days
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(3.32,0.7,"Tempo Decorrido: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(3,0.7,f"{tempo_decorrido} dias", border=True, align="C")
        
        #Cria o saldo de prazo
        saldo_prazo = (diario.obra.termino - diario.data).days
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(3.16,0.7,"Saldo de Prazo: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(3.16,0.7,f"{saldo_prazo} dias", border=True, align="C", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco
        
        #Cria a linha com a data que o diario foi registrado e que dia da semana é
        
        #Cria os campos de data atual
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(3.16,0.7,"Data: ", border=True, align="R", fill=True)
        pdf.set_font('helvetica', size=8)
        pdf.cell(3.16,0.7,f"{diario.data.strftime("%d/%m/%Y")}", border=True, align="C")
        
        #Cria as colunas de dia da semana e muda a cor caso seja o dia da semana correspondente
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(6.32,0.7,"Dia da Semana: ", border=True, align="R", fill=True)
        
        #Descobre qual dia da semana é a data do diario
        dia_semana = dia_da_semana(diario.data)
        #Troca o fundo da célula pra verde claro para realçar o dia da semana correspondente à data do diário
        pdf.set_fill_color(146,208,80)

        #Cria os dias da semana
        pdf.set_font('helvetica', 'B', size=8)
        pdf.cell(0.9028, 0.7, 'Seg',fill=True if dia_semana == "segunda" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Ter",fill=True if dia_semana == "terca" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Qua",fill=True if dia_semana == "quarta" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Qui",fill=True if dia_semana == "quinta" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Sex",fill=True if dia_semana == "sexta" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Sáb",fill=True if dia_semana == "sabado" else False, border=True, align="C")
        pdf.cell(0.9028, 0.7, "Dom", new_x='LMARGIN', new_y='NEXT',fill=True if dia_semana == "domingo" else False, border=True, align="C")
        
        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco

        #retorna a cor de fundo pra cinza para os próximos enunciados manterem o padrão
        pdf.set_fill_color(200, 200, 200)
        
        #Cria as coluna de turno e tempo
        pdf.set_font('helvetica', "B", size=10)
        pdf.cell(0,0.5,"Turno/Tempo", align="C", border=True, fill=True, new_x='LMARGIN', new_y='NEXT')

        pdf.cell(h=0.1, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco
        
        #Linha das imagens do tempo
        pdf.image('images\\clima-relatorio.jpeg',w=19, keep_aspect_ratio=True)
        
        #Linha da manhã
        pdf.cell(5,0.5,"Manhã", align="C", border=True, fill=True)
        #Troca o fundo da célula pra verde claro para realçar o clima registrado para aquele turno de serviço
        pdf.set_fill_color(146,208,80)
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_manha == "Limpo" else False)#Limpo
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_manha == "Nublado" else False)#Nublado
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_manha == "Chuva" else False)#Chuva
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_manha == "Impraticável" else False
        ,new_x='LMARGIN', new_y='NEXT')#Impraticável

        #Linha da tarde
        #retorna a cor de fundo pra cinza para os próximos enunciados manterem o padrão
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(5,0.5,"Tarde", align="C", border=True, fill=True)
        #Troca o fundo da célula pra verde claro para realçar o clima registrado para aquele turno de serviço
        pdf.set_fill_color(146,208,80)
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_tarde == "Limpo" else False)#Limpo
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_tarde == "Nublado" else False)#Nublado
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_tarde == "Chuva" else False)#Chuva
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_tarde == "Impraticável" else False
        ,new_x='LMARGIN', new_y='NEXT')#Impraticável

        #Linha da noite
        #retorna a cor de fundo pra cinza para os próximos enunciados manterem o padrão
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(5,0.5,"Noite", align="C", border=True, fill=True)
         #Troca o fundo da célula pra verde claro para realçar o clima registrado para aquele turno de serviço
        pdf.set_fill_color(146,208,80)
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_noite == "Limpo" else False)#Limpo
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_noite == "Nublado" else False)#Nublado
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_noite == "Chuva" else False)#Chuva
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_noite == "Impraticável" else False
        ,new_x='LMARGIN', new_y='NEXT')#Impraticável

        #Linha da madrugada
        #retorna a cor de fundo pra cinza para os próximos enunciados manterem o padrão
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(5,0.5,"Madrugada", align="C", border=True, fill=True)
        #Troca o fundo da célula pra verde claro para realçar o clima registrado para aquele turno de serviço
        pdf.set_fill_color(146,208,80)
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_madrugada == "Limpo" else False)#Limpo
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_madrugada == "Nublado" else False)#Nublado
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_madrugada == "Chuva" else False)#Chuva
        pdf.cell(3.48,0.5,"", align="C", border=True, fill=True if diario.clima_madrugada == "Impraticável" else False,new_x='LMARGIN', new_y='NEXT')#Impraticável

        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco

        #Cria a tabela produção diária
        #Cria os cabeçalhos
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(0,0.5,"Produção Diária", fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT')
        pdf.cell(9,0.5,"Descrição dos Serviços", fill=True, align="C", border=True)
        pdf.cell(1,0.5,"Item",fill=True, align="C", border=True)
        pdf.cell(9,0.5,"Referência", fill=True, align="C", border=True,new_x='LMARGIN', new_y='NEXT')

        #Preenche a tabela com os serviços cadastrados
        pdf.set_fill_color("#FFFFFF")
        pdf.set_font('',size=6)
        dados_servico = []
        for servico in diario.servicos:
            servico_da_vez = [f"{servico.servicos_padrao.descricao}",f"{servico.item}", f"{servico.referencia}"]
            dados_servico.append(servico_da_vez)
        # Garante que a tabela tenha 14 linhas, adicionando linhas vazias se necessário
        total_linhas = 14
        linhas_vazias = total_linhas - len(dados_servico)
        for _ in range(linhas_vazias):
            dados_servico.append(["", "", ""])  # Adiciona uma linha vazia com três colunas
        #Cria a tabela usando table do FPDF
        with pdf.table(text_align="CENTER", col_widths=(9,1,9), first_row_as_headings=False, line_height=0.5) as table:
            for linha_tabela in dados_servico:
                linha = table.row()
                for dados in linha_tabela:
                    linha.cell(dados)
        
        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco

        #Cria a tabela de funções diretas e indiretas
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font(style="B", size=10)
        pdf.cell(0,0.5,"Efetivo Alocado", fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT')
        pdf.cell(12,0.5, "Mão de Obra Direta", fill=True, align="C", border=True)
        pdf.cell(7,0.5, "Mão de Obra Indireta", fill=True, align="C", border=True,new_x='LMARGIN', new_y='NEXT')
        #Função, Quantidade, Presente, Ausente, Efetivo    Descrição, Efetivo
        pdf.set_font(style="B", size=8)
        pdf.cell(5,0.5, "Função", fill=True, align="C", border=True)
        pdf.cell(2,0.5, "Quantidade", fill=True, align="C", border=True)
        pdf.cell(1.5,0.5, "Presente", fill=True, align="C", border=True)
        pdf.cell(1.5,0.5, "Ausente", fill=True, align="C", border=True)
        pdf.cell(2,0.5, "Efetivo", fill=True, align="C", border=True)
        pdf.cell(5,0.5, "Descrição", fill=True, align="C", border=True)
        pdf.cell(2,0.5, "Efetivo", fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT')
        #Dados da tabela
        #Inicia a montagem das tabelas, elas serão montadas ao mesmo tempo, lado a lado
        
        pdf.set_font(style='')
        pdf.set_fill_color(255,255,255)
        for funcao_direta, funcao_indireta in zip(diario.efetivo_direto, diario.efetivo_indireto):
            pdf.cell(5,0.5, funcao_direta.funcao, fill=True, align="C", border=True)
            pdf.cell(2,0.5, f"{funcao_direta.qtde}", fill=True, align="C", border=True)
            pdf.cell(1.5,0.5, f"{funcao_direta.presente}", fill=True, align="C", border=True)
            pdf.cell(1.5,0.5, f"{funcao_direta.qtde - funcao_direta.presente}", fill=True, align="C", border=True)
            pdf.cell(2,0.5, f"{funcao_direta.presente}", fill=True, align="C", border=True)
            pdf.cell(5,0.5, funcao_indireta.funcao, fill=True, align="C", border=True)
            pdf.cell(2,0.5, f"{funcao_indireta.efetivo}", fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT')
        
        pdf.cell(h=0.2, w=0,new_x='LMARGIN', new_y='NEXT',text='') #linha em branco

        #Campo de observações
        if diario.fotos:
            msg = "\n NÃO HÁ FOTOS REGISTRADAs PARA ESSE DIÁRIO."
        else:
            msg = ""
            
        pdf.set_font(style="B", size=6)
        pdf.set_fill_color(200,200,200)
        pdf.cell(0,0.7,"Observações", fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT')
        pdf.set_fill_color(255,255,255)
        pdf.cell(0,1,diario.observacoes+msg, fill=True, align="C", new_x='LMARGIN', new_y='NEXT')

        # Configurações iniciais do cabeçalho
        pdf.set_font(style="B", size=14)
        pdf.set_fill_color(255, 255, 255)
        
        if diario.fotos:
            # Configurações gerais
            col_width = pdf.epw / 2  # Divide a largura da página em 2 colunas
            row_height = (pdf.h - pdf.t_margin - pdf.b_margin) / 4  # Divide o espaço restante em 4 linhas
            images_per_page = 6  # Total de imagens por página

            # Divide as fotos em grupos de 6 para cada página
            grupos_fotos = [diario.fotos[i:i + images_per_page] for i in range(0, len(diario.fotos), images_per_page)]

            # Itera sobre os grupos de fotos para criar páginas
            for grupo in grupos_fotos:
                pdf.add_page()

                # Insere uma célula no topo da página
                pdf.set_font("helvetica", "B", 12)  # Configura a fonte para o cabeçalho
                pdf.cell(
                0, 0.7, f"RELATÓRIO FOTOGRÁFICO {diario.data.strftime("%d/%m/%Y")}",
                fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT'
            )
                with pdf.table(
                    col_widths=[col_width] * 2,  # Duas colunas de largura igual
                    line_height=row_height,
                    text_align="CENTER",
                    first_row_as_headings=False,
                    borders_layout="NONE"
                ) as table:
                    for i in range(0, len(grupo), 2):  # Adiciona fotos em pares (2 por linha)
                        linha = table.row()
                        for foto in grupo[i:i + 2]:  # Garante que não exceda o número de colunas
                            linha.cell(img=foto.caminho_arquivo, img_fill_width=True)

            # Posiciona a imagem final no rodapé, se necessário
            altura = 1
            largura = 12
            y_pos = pdf.h - pdf.b_margin - altura  # Altura total - margem inferior - altura da imagem
            x_pos = (pdf.w - largura) / 2  # Centraliza a imagem horizontalmente

            pdf.image('images\\campo_assinatura.png', x=x_pos, y=y_pos, w=largura, keep_aspect_ratio=True)
        
        else:
            # Insere uma célula no topo da página
            pdf.set_font("helvetica", "B", 12)  # Configura a fonte para o cabeçalho
            pdf.cell(
                0, 0.7, f"RELATÓRIO FOTOGRÁFICO {diario.data.strftime("%d/%m/%Y")}",
                fill=True, align="C", border=True, new_x='LMARGIN', new_y='NEXT'
                        )

            # Posiciona a imagem final no rodapé, se necessário
            altura = 1
            largura = 12
            y_pos = pdf.h - pdf.b_margin - altura  # Altura total - margem inferior - altura da imagem
            x_pos = (pdf.w - largura) / 2  # Centraliza a imagem horizontalmente

            pdf.image('images\\campo_assinatura.png', x=x_pos, y=y_pos, w=largura, keep_aspect_ratio=True)
        
    pdf_temporario = io.BytesIO()
    pdf.output(pdf_temporario)
    pdf_temporario.seek(0)
    return pdf_temporario
            