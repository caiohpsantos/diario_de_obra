import streamlit as st
from datetime import datetime
from models import session, Contrato, Obra, Diario, Foto, Base

def salvar_fotos_na_pasta(id_diario, arquivos):

    '''
        Salva os arquivos fornecidos na pasta correspondente, troca o nome dele para
        a palavra 'diario', o id do diario, a palavra 'arquivo' e o número de arquivos que 
        estão gravados pra aquele diário. 
        Exemplo: diario_7_arquivo_2.jpg
        7 é o número do diario
        2 é o terceiro arquivo cadastrado para aquela entrada do diário

        :param id_diario: Integer, número de id do diario ao qual o(s) arquivo(s) se refere(m)
        :param arquivos: Objeto, arquivos fornecidos no formulário de registro do diário como foram upados
        :return: Lista de String, o caminho completo de cada arquivo fornecido para registro no bd
    '''
    caminho_arquivos = []

    '''Consulta no banco de dados se já existem arquivos cadastrados para a entrada do,
    caso existam retorna a qtde de registros encontrados, caso não existam retorna 0
    '''

    contagem_fotos = session.query(func.count(Foto.id)).filter(Foto.diario_id == id_diario).scalar()
    
    st.write(contagem_fotos)


    # for index, arquivo in enumerate(arquivos):
    #     extensao = os.path.splitext(arquivo.name)[1]  # Obtém a extensão do arquivo, incluindo o ponto
    #     '''O nome do arquivo usa o número de resultados para somar à qtde de arquivos que já existem 
    #     para impedir que seja sobreescritos'''
    #     nome_arquivo = f"{id_os}_{id_cliente}_arquivo_{index + num_arquivos_existentes}{extensao}"
    #     caminho_destino = os.path.join(DIR_MIDIA_OS, nome_arquivo)
    #     try:
    #         with open(caminho_destino, "wb") as f:
    #                 f.write(arquivo.getbuffer() if hasattr(arquivo, 'getbuffer') else arquivo)
    #                 caminho_arquivos.append(caminho_destino)
    #     except Exception as e:
    #             print(f"Erro ao salvar o arquivo {arquivo}: {e}")
    # return caminho_arquivos

def novo_diario():
    st.title("Novo diário de obra")

    '''Pesquisa todos os contratos e cria um selecbox com as opções'''
    contrato_do_diario = None
    contratos = session.query(Contrato).all()
    opcoes_contratos = {f"{contrato.numero} / {contrato.nome}":contrato.numero for contrato in contratos}
    contrato_selecionado = st.selectbox("Selecione o contrato", ['']+list(opcoes_contratos.keys()))
    contrato_selecionado_id = opcoes_contratos.get(contrato_selecionado)
    if contrato_selecionado_id:
        contrato_do_diario = session.query(Contrato).filter_by(numero=contrato_selecionado_id).first()
    
    '''Pesquisa todas as obras cadastradas para o contrato selecionado e cria um selectbox com as obras encontradas'''
    obra_do_diario = None
    if contrato_do_diario:
        obras = session.query(Obra).filter_by(contrato_numero=contrato_do_diario.numero).all()
        opcoes_obras = {obra.nome:obra.id for obra in obras}
        obra_selecionada = st.selectbox("Selecione a obra", ['']+list(opcoes_obras.keys()))
        obra_selecionada_id = opcoes_obras.get(obra_selecionada)
        if obra_selecionada_id:
            obra_do_diario = session.query(Obra).filter_by(id=obra_selecionada_id).first()

    st.divider()

    if obra_do_diario:
        
        data = st.date_input("Data da vistoria", format="DD/MM/YYYY", value=datetime.today())

        st.divider()

        col1,col2,col3 = st.columns(3)
        
        opcoes_clima = ["Ensolarado", "Nublado", "Chovendo", "Impossível"]

        with col1:
            clima_manha = st.radio("**CLIMA DA MANHÃ**", opcoes_clima,)

        with col2:
            clima_tarde = st.radio("**CLIMA DA TARDE**", opcoes_clima)

        with col3:
            clima_noite = st.radio("**CLIMA DA NOITE**", opcoes_clima)

        st.divider()

        fotos = st.file_uploader("Adicione as fotos", ["jpg", "jpeg", "png", "bmp"], True)

        



        
        
        

        

