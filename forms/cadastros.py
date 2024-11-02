import streamlit as st
from datetime import datetime
from models import session, Contrato, Obra, Base

def cad_contrato():
    with st.form("form_cadastro_contratos"):
        
        st.title("Cadastro de Contratos")
        
        st.divider()

        numero = st.text_input("Número do Contrato").upper()

        nome = st.text_input("Nome do contrato").upper()

        cliente = st.text_input("Cliente").upper()

        gravar = st.form_submit_button("Gravar")

        if gravar:
            
            problema = False

            '''Verifica se todos os campos foram preenchidos'''
            if not numero or not nome or not cliente:
                st.error("Todos os campos devem ser preenchidos")
                problema = True
            
            '''Verifica se o numero do contrato ou seu nome já existem'''
            if session.query(Contrato).filter_by(numero=numero).first() is not None:
                st.error("Esse numero de contrato já está em uso")
                problema = True

            if session.query(Contrato).filter_by(nome=nome).first() is not None:
                st.error("Esse nome de contrato já está em uso")
                problema = True
            
            '''Se não houver nenhum problema, realiza o cadastro'''
            if not problema:
                contrato = Contrato(ativo=True, numero=numero, nome=nome, cliente=cliente)
                session.add(contrato)
                session.commit()
                st.success(f"Contrato: {contrato} foi adicionado com sucesso.")

def edit_contrato():
    '''Pesquisa todos os contratos e cria um selecbox para selecionar qual deve ser editado'''
    contrato_pra_editar = None
    contratos = session.query(Contrato).all()
    opcoes = {f"{contrato.numero} / {contrato.nome}":contrato.numero for contrato in contratos}
    selecionado = st.selectbox("Selecione o contrato para edição", ['']+list(opcoes.keys()))
    selecionado_id = opcoes.get(selecionado)
    if selecionado_id:
        contrato_pra_editar = session.query(Contrato).filter_by(numero=selecionado_id).first()

    '''repete o formulário do cadastro, inserindo os dados do contrato como values dos campos'''
    
    if contrato_pra_editar:
    
        with st.form("form_editar_contratos"):
           
            st.title("Edição de Contratos")
            st.divider()

            # Determina a situação com base no estado atual do contrato
            situacao = 'Marque aqui para desativar esse contrato' if contrato_pra_editar.ativo else 'Marque aqui para ativar esse contrato'
            ativo_editado = st.checkbox(situacao, contrato_pra_editar.ativo, help="Ao deixar essa opção marcada, este contrato pode ter mais obras cadastradas e pode ter diários registrados.")

            numero = st.text_input("Número do Contrato", value=contrato_pra_editar.numero, disabled=True).upper()
            nome_editado = st.text_input("Nome do contrato", value=contrato_pra_editar.nome).upper()
            cliente_editado = st.text_input("Cliente", value=contrato_pra_editar.cliente).upper()

            gravar = st.form_submit_button("Gravar")

            if gravar:
                problema = False

                # Verifica se houve alteração em qualquer campo
                campos_alterados = (
                    ativo_editado != contrato_pra_editar.ativo or
                    nome_editado != contrato_pra_editar.nome.upper() or
                    cliente_editado != contrato_pra_editar.cliente.upper()
                )

                # Executa as verificações somente se houver alterações
                if campos_alterados:
                    # Verifica se todos os campos foram preenchidos
                    if not nome_editado or not cliente_editado:
                        st.error("Todos os campos devem ser preenchidos")
                        problema = True

                    # Verifica se o nome do contrato já existe
                    if nome_editado != contrato_pra_editar.nome.upper() and session.query(Contrato).filter_by(nome=nome_editado).first() is not None:
                        st.error("Esse nome de contrato já está em uso")
                        problema = True

                    # Se não houver nenhum problema, realiza a alteração
                    if not problema:
                        contrato_pra_editar.ativo = ativo_editado
                        contrato_pra_editar.nome = nome_editado
                        contrato_pra_editar.cliente = cliente_editado
                        session.commit()
                        st.success(f"Contrato: {contrato_pra_editar} foi alterado com sucesso.")
                else:
                    st.info("Nenhuma alteração foi detectada.")
   
def cad_obra():
    contratos = session.query(Contrato).filter_by(ativo=True).all()
    contratos_opcoes = {f"{contrato.numero} - {contrato.nome}":contrato.numero for contrato in contratos}
    
    if contratos_opcoes:
        with st.form("form_cadastro_obra"):

            st.title("Cadastro de Obras")

            st.divider()

            nome_obra = st.text_input("Nome da Obra").upper()

            local = st.text_input("Local da Obra").upper()

            data_inicio = st.date_input("Data de Início", format="DD/MM/YYYY", value=datetime.today())

            data_termino = st.date_input("Data do Término", format="DD/MM/YYYY", min_value=datetime.today())

            contrato_id = st.selectbox("Contrato", options=['']+list(contratos_opcoes.keys()))
            
            gravar_obra = st.form_submit_button("Cadastrar Obra")
            
            if gravar_obra:
                problema = False
                '''Verifica se todos os campos foram preenchidos'''
                if not nome_obra or not local:
                    st.error("Preencha todos os campos")
                    problema=True
                
                '''Verifica se o nome da obra já está em uso'''
                if session.query(Obra).filter_by(nome=nome_obra).first() is not None:
                    st.error("Já existe uma obra com esse nome")
                    problema = True
                
                '''Verifica se as data de inicio e termino são as mesmas'''
                if data_inicio == data_termino:
                    st.error("Selecione as datas de início e término para a obra")
                    problema = True

                '''Verifica se foi escolhido um contrato'''
                if contrato_id == '':
                    st.error("Selecione um contrato, a seleção está vazia")
                    problema = True

                if problema == False:
                    nova_obra = Obra(ativo=True, nome=nome_obra, local=local, inicio=data_inicio, termino=data_termino, contrato_numero=contratos_opcoes[contrato_id])
                    session.add(nova_obra)
                    session.commit()
                    contrato_da_obra = session.query(Contrato).filter_by(numero=nova_obra.contrato_numero).first()
                    st.success(f"Nova obra cadastrada com sucesso para o contrato {contrato_da_obra.nome}!")
    else:
        st.warning("Não há contratos ativos para cadastrar novas obras ou não há contratos cadastrados.")
            
def edit_obra():
    '''Pesquisa todos os contratos e cria um selecbox com as opções'''
    contrato_da_obra = None
    contratos = session.query(Contrato).filter_by(ativo=True).all()
    opcoes_contratos = {f"{contrato.numero} / {contrato.nome}":contrato.numero for contrato in contratos}
    contrato_selecionado = st.selectbox("Selecione o contrato", ['']+list(opcoes_contratos.keys()))
    contrato_selecionado_id = opcoes_contratos.get(contrato_selecionado)
    if contrato_selecionado_id:
        contrato_da_obra = session.query(Contrato).filter_by(numero=contrato_selecionado_id).first()
    
    '''Pesquisa todas as obras cadastradas para o contrato selecionado e cria um selectbox para escolher a obra para edição'''
    obra_pra_editar = None
    if contrato_da_obra:
        obras = session.query(Obra).filter_by(contrato_numero=contrato_da_obra.numero).all()
        opcoes_obras = {obra.nome:obra.id for obra in obras}
        obra_selecionada = st.selectbox("Selecione a obra para edição", ['']+list(opcoes_obras.keys()))
        obra_selecionada_id = opcoes_obras.get(obra_selecionada)
        if obra_selecionada_id:
            obra_pra_editar = session.query(Obra).filter_by(id=obra_selecionada_id).first()
    
    '''repete o formulário do cadastro, inserindo os dados do contrato como values dos campos'''
    if obra_pra_editar:
       with st.form("form_cadastro_obra"):

            st.title("Edição de Obras")
            st.divider()

            # Determina a situação com base no estado atual da obra
            situacao = 'Marque aqui para desativar essa obra' if obra_pra_editar.ativo else 'Marque aqui para ativar essa obra'
            ativo_editado = st.checkbox(situacao, obra_pra_editar.ativo, help="Ao deixar essa opção marcada, essa obra pode ter diários registrados.")

            nome_obra_editado = st.text_input("Nome da Obra", value=obra_pra_editar.nome).upper()
            local_editado = st.text_input("Local da Obra", value=obra_pra_editar.local).upper()
            data_inicio_editado = st.date_input("Data de Início", value=obra_pra_editar.inicio)
            data_termino_editado = st.date_input("Data de Término", value=obra_pra_editar.termino)
            
            gravar_obra = st.form_submit_button("Gravar alterações")
            
            if gravar_obra:
                problema = False

                # Verifica se houve alterações em qualquer campo
                campos_alterados = (
                    ativo_editado != obra_pra_editar.ativo or
                    nome_obra_editado != obra_pra_editar.nome or
                    local_editado != obra_pra_editar.local or
                    data_inicio_editado != obra_pra_editar.inicio or
                    data_termino_editado != obra_pra_editar.termino
                )

                if campos_alterados:
                    # Verifica se todos os campos foram preenchidos
                    if not nome_obra_editado or not local_editado:
                        st.error("Preencha todos os campos.")
                        problema = True
                    
                    # Verifica se o nome da obra já está em uso, excluindo a obra atual da busca
                    obra_existente = session.query(Obra).filter_by(nome=nome_obra_editado).first()
                    if obra_existente and obra_existente.id != obra_pra_editar.id:
                        st.warning("Esse nome de obra já está em uso. Por favor, escolha outro.")
                        problema = True

                    # Se não houver nenhum problema, salva as alterações
                    if not problema:
                        obra_pra_editar.ativo = ativo_editado
                        obra_pra_editar.nome = nome_obra_editado
                        obra_pra_editar.local = local_editado
                        obra_pra_editar.inicio = data_inicio_editado
                        obra_pra_editar.termino = data_termino_editado
                        session.commit()
                        st.success(f"A Obra '{obra_pra_editar.nome}' do contrato '{contrato_da_obra}' foi alterada com sucesso.")
                else:
                    st.info("Nenhuma alteração foi detectada.")
