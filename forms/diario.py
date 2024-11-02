import os
import yaml
import streamlit as st
from time import sleep
from yaml import SafeLoader
from datetime import datetime, timedelta
from models import session, Contrato, Obra, Diario, Foto, Servicos, Efetivo_Direto, Efetivo_Indireto, Base
from .funcionalidades import salvar_fotos_na_pasta
from sqlalchemy import func

def novo_diario():
    st.title("Novo diário de obra")

    '''Pesquisa todos os contratos e cria um selecbox com as opções'''
    contrato_do_diario = None
    contratos = session.query(Contrato).filter_by(ativo=True).all()
    opcoes_contratos = {f"{contrato.numero} / {contrato.nome}":contrato.numero for contrato in contratos}
    contrato_selecionado = st.selectbox("Selecione o contrato", ['']+list(opcoes_contratos.keys()))
    contrato_selecionado_id = opcoes_contratos.get(contrato_selecionado)
    if contrato_selecionado_id:
        contrato_do_diario = session.query(Contrato).filter_by(numero=contrato_selecionado_id).first()
    
    '''Pesquisa todas as obras cadastradas para o contrato selecionado e cria um selectbox com as obras encontradas'''
    obra_do_diario = None
    if contrato_do_diario:
        obras = session.query(Obra).filter_by(contrato_numero=contrato_do_diario.numero, ativo=True).all()
        opcoes_obras = {obra.nome:obra.id for obra in obras}
        obra_selecionada = st.selectbox("Selecione a obra", ['']+list(opcoes_obras.keys()))
        obra_selecionada_id = opcoes_obras.get(obra_selecionada)
        if obra_selecionada_id:
            obra_do_diario = session.query(Obra).filter_by(id=obra_selecionada_id).first()

    st.divider()

    if obra_do_diario:
        st.subheader("Data")

        data = st.date_input("Data", format="DD/MM/YYYY", value=datetime.today(),label_visibility='hidden')

        st.divider()

        st.subheader("Turno/Tempo")

        col_manha,col_tarde,col_noite = st.columns(3)
        
        opcoes_clima = ["Limpo", "Nublado", "Chuva", "Impraticável"]

        with col_manha:
            clima_manha = st.radio("**CLIMA DA MANHÃ**", opcoes_clima)

        with col_tarde:
            clima_tarde = st.radio("**CLIMA DA TARDE**", opcoes_clima)

        with col_noite:
            clima_noite = st.radio("**CLIMA DA NOITE**", opcoes_clima)

        st.divider()

        st.subheader("Produção Diária")

        producao = {}

        num_campos_servicos = st.slider("Quantos serviços foram feitos", min_value=1, max_value=14, value=1)

        col_servico, col_descricao = st.columns(2)
        for i in range(num_campos_servicos):
            with col_servico:
                descricao = st.text_input(f"Descrição do Serviço {i + 1}", key=f"descricao_do_servico_{i}").upper()
            with col_descricao:
                referencia = st.text_input(f"Referência {i + 1}", key=f"referencia_{i}").upper()
            
            if descricao and referencia:
                producao[i + 1] = {'descricao': descricao, 'referencia': referencia}

        st.divider()

        st.subheader("Efetivo Alocado")

        efetivo_direto = {}
        efetivo_indireto = {}

        efetivo_padrao = st.radio("Usar efetivo padrão", ["Sim", "Digitar Efetivo"], horizontal=True)

        if efetivo_padrao == "Sim":
            efetivo_direto = {
                'TOPÓGRAFO':{
                    'qtde':1,
                    'presente':1,
                    'ausente':0,
                    'efetivo':1
                },
                'AUX. DE TOPOGRAFIA':{
                    'qtde':2,
                    'presente':2,
                    'ausente':0,
                    'efetivo':2
                },
                'LABORATORISTA':{
                    'qtde':2,
                    'presente':2,
                    'ausente':0,
                    'efetivo':2
                }
            }
            efetivo_indireto = {
                "ENGENHEIRO SUPERVISOR": 1,
                "ENGENHEIRO RESIDENTE": 1,
                "ENG. DE PLAN. E PROJETOS":1
            }

            col_direto, col_indireto = st.columns(2)
            with col_direto:
                st.text("Efetivo Direto")
                st.table(efetivo_direto)
            
            with col_indireto:
                st.text("Efetivo Indireto")
                st.table(efetivo_indireto)
            
        else:
            st.text("Efetivo Direto")
            
            num_campos_funcao_direta = st.slider("Quantas funções diretas", min_value=1, max_value=5, value=3)

            for i in range(num_campos_funcao_direta):
                
                col_funcao, col_qtde, col_presente, col_ausente, col_efetivo = st.columns([2,1,1,1,1])

                with col_funcao:
                    funcao = st.text_input(f"Função {i+1}", key=f"funcao_{i}").upper()
                with col_qtde:
                    qtde = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1)
                with col_presente:
                    presente = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0)
                with col_ausente:
                    ausente = st.number_input("Ausente", key=f"ausente_{i}", step=1, value=qtde-presente, disabled=True, min_value=0)
                with col_efetivo:
                    efetivo = st.number_input("Efetivo", disabled=True, key=f'efetivo_{i}', step=1, value=qtde-ausente)
                
                if funcao and qtde:
                    efetivo_direto[funcao] = {
                        'qtde': qtde, 
                        'presente':presente,
                        'ausente':ausente, 
                        'efetivo':efetivo
                        }
                    


            st.text("Efetivo Indireto")
            num_campos_funcao_indireta = st.slider("Quantas funções indiretas", min_value=1, max_value=5, value=3)
            for i in range(num_campos_funcao_indireta):
            
                col_funcao, col_efetivo = st.columns([2,1])

                with col_funcao:
                    funcao =  st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}").upper()

                with col_efetivo:
                    efetivo = st.number_input("Efetivo", key=f'efetivo_indireto_{i}', step=1)

                if funcao:
                    efetivo_indireto[funcao] = efetivo
        
        st.divider()

        st.subheader("Observações")

        observacoes = st.text_area("Digite as observações").upper()

        st.divider()

        st.subheader("Registro Fotográfico")

        fotos = st.file_uploader("Adicione as fotos", ["jpg", "jpeg", "png", "bmp"], True)

        gravar = st.button("Gravar")

        if gravar:

            problema = False

            if not clima_manha or not clima_tarde or not clima_noite:
                st.error("Selecione o clima para todos os turnos")
                problema = True

            if efetivo_padrao == "Digitar Efetivo" and (efetivo_direto == {} or efetivo_indireto == {}):
                st.error("Foi escolhida a opção de digitar o efetivo alocado, porém não foram registradas nenhuma função ou quantidade de pessoas.")
                problema = True

            if not fotos:
                st.error("Não há fotos registradas para este diário. Verifique acima.")
                problema = True

            if session.query(Diario).filter_by(obra_id = obra_do_diario.id, data=data).first() is not None:
                st.error("Já existe um diário gravado para esta data")
                problema = True
            
            if problema == False:
                # efetivo_direto, efetivo_indireto, observacoes, fotos

                # Gravar o diário
                novo_diario = Diario(
                    data=data, 
                    clima_manha=clima_manha, 
                    clima_tarde=clima_tarde, 
                    clima_noite=clima_noite, 
                    observacoes=observacoes, 
                    obra_id = obra_do_diario.id)
                session.add(novo_diario)
                session.commit()

                # Gravar os serviços
                for item, dados_servico in producao.items():
                    novo_servico = Servicos(
                        descricao = dados_servico['descricao'], 
                        item=item, 
                        referencia=dados_servico['referencia'], 
                        diario_id=novo_diario.id)
                    session.add(novo_servico)
                    session.commit()
                
                
                # Gravar os efetivos diretos e indiretos
                for funcao, dados in efetivo_direto.items():
                    novo_efetivo_direto = Efetivo_Direto(
                        funcao=funcao,
                        qtde=dados['qtde'],
                        presente=dados['presente'],
                        diario_id=novo_diario.id
                    )
                    session.add(novo_efetivo_direto)
                    session.commit()
                
                for funcao, qtde in efetivo_indireto.items():
                    novo_efetivo_indireto = Efetivo_Indireto(
                        funcao=funcao,
                        efetivo=qtde,
                        diario_id = novo_diario.id
                    )
                    session.add(novo_efetivo_indireto)
                    session.commit()

                # Gravar as fotos
                
                caminho_arquivos_salvos = salvar_fotos_na_pasta(contrato_do_diario, obra_do_diario, novo_diario, fotos)

                for caminho in caminho_arquivos_salvos:
                    nova_foto = Foto(
                        caminho_arquivo = caminho,
                        diario_id = novo_diario.id
                        )
                    session.add(nova_foto)
                    session.commit()
                
                st.success("Diário de Obra gravado com sucesso")

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

def edita_diario():

    # Formulário de Pesquisa para Edição de Diário
        st.title("Pesquisa de Diários para Edição", help="Pode usar apenas 1 opção ou combinar várias")

        # Filtro de Contrato/Obra
        contratos = session.query(Contrato).filter_by(ativo=True).all()  # Obtém todos os contratos ativos
        contratos_opcoes = {contrato.nome: contrato.numero for contrato in contratos}
        contrato_selecionado = st.selectbox("Selecione o Contrato (opcional)", options=[""] + list(contratos_opcoes.keys()))

        obra_selecionada = None  # Inicializa a variável de obra
        if contrato_selecionado:
            obras = session.query(Obra).filter_by(contrato_numero=contratos_opcoes[contrato_selecionado], ativo=True).all()
            obras_opcoes = {obra.nome: obra.id for obra in obras}
            obra_selecionada = st.selectbox("Selecione a Obra (opcional)", options=[""] + list(obras_opcoes.keys()))
        
        st.divider()

        # Filtro de Data do Diário
        data_especifica = st.date_input("Data do Diário (opcional)", format="DD/MM/YYYY", value=None)

        st.divider()

        # Filtro de Número do Diário
        numero_diario = st.number_input("Número de Identificação do Diário (opcional)", step=1)

        # Filtro de Intervalo de Dias
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Inicial (opcional)", value=datetime.today() - timedelta(days=7))
        with col2:
            data_fim = st.date_input("Data Final (opcional)", value=datetime.today())

      
        # Verifica o intervalo de datas válido, caso as datas sejam informadas
        if data_inicio > data_fim:
            st.error("A data inicial deve ser anterior ou igual à data final.")
        else:
            # Base da consulta
            query = session.query(Diario).join(Obra).join(Contrato)

            # Aplica filtros selecionados
            if contrato_selecionado:
                query = query.filter(Contrato.numero == contratos_opcoes[contrato_selecionado])
            if obra_selecionada:
                query = query.filter(Obra.id == obras_opcoes[obra_selecionada])
            if data_especifica:
                query = query.filter(Diario.data == data_especifica)
            if data_inicio and data_fim:
                query = query.filter(Diario.data.between(data_inicio, data_fim))
            if numero_diario:
                query = query.filter(Diario.id == numero_diario)

            # Executa a pesquisa
            diarios_resultados = query.all()

            # Exibe os resultados
            if diarios_resultados:

                diario_opcoes = {f"{d.data.strftime('%d/%m/%Y')} - {d.obra.contrato.nome} - {d.obra.nome} - DIÁRIO {d.id}": d for d in diarios_resultados}
                diario_selecionado = st.radio("Selecione um Diário:", list(diario_opcoes.keys()), index=None)
                if diario_selecionado:
                    diario_selecionado_obj = diario_opcoes[diario_selecionado]
                    # Gera as abas para edição quando há um diario_selecionado no radio                
                    tab_tempo, tab_producao, tab_efetivo, tab_foto = st.tabs(["Data/Tempo", "Produção", "Efetivo", "Fotos"])

                    with tab_tempo:
                        st.subheader("Data")

                        data = st.date_input("Data", format="DD/MM/YYYY", value=diario_selecionado_obj.data,label_visibility='hidden')

                        st.divider()

                        st.subheader("Turno/Tempo")

                        col_manha,col_tarde,col_noite = st.columns(3)
                        
                        opcoes_clima = ["Limpo", "Nublado", "Chuva", "Impraticável"]

                        with col_manha:
                            clima_manha = st.radio("**CLIMA DA MANHÃ**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_manha))

                        with col_tarde:
                            clima_tarde = st.radio("**CLIMA DA TARDE**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_tarde))

                        with col_noite:
                            clima_noite = st.radio("**CLIMA DA NOITE**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_noite))

                        gravar = st.button("Gravar Alterações", help="Apenas as informações dessa aba serão alteradas")

                        if gravar:

                            problema = False
                            
                            campos_alterados = (
                                diario_selecionado_obj.data != data or
                                diario_selecionado_obj.clima_manha != clima_manha or
                                diario_selecionado_obj.clima_tarde != clima_tarde or
                                diario_selecionado_obj.clima_noite != clima_noite
                            )

                            if campos_alterados:
                                if not data:
                                    st.error("O campo data não pode ficar vazio")
                                    problema = True

                                if not problema:
                                    diario_selecionado_obj.data = data
                                    diario_selecionado_obj.clima_manha = clima_manha
                                    diario_selecionado_obj.clima_tarde = clima_tarde
                                    diario_selecionado_obj.clima_noite = clima_noite
                                    session.commit()
                                    st.success(f"Os dados de Tempo/Turno do diário nº {diario_selecionado_obj.id} do contrato {diario_selecionado_obj.obra.contrato.nome} obra {diario_selecionado_obj.obra.nome} foram alterados com sucesso.")
                            
                            else:
                                st.info("Nenhuma alteração foi detectada")
                                            
                    with tab_producao:
                        st.subheader("Produção Diária")

                        # Contagem atual de serviços para definir o valor inicial do slider
                        contagem_servicos = session.query(func.count(Servicos.id)).filter(Servicos.diario_id == diario_selecionado_obj.id).scalar()

                        # Slider para selecionar o número de serviços
                        num_campos_servicos = st.slider("Quantos serviços foram feitos", min_value=1, max_value=14, value=contagem_servicos)

                        # Obtenha os serviços cadastrados
                        servicos_cadastrados = session.query(Servicos).filter_by(diario_id=diario_selecionado_obj.id).all()

                        # Dicionário para armazenar a produção
                        producao = {}

                        # Cria campos de entrada de acordo com o número selecionado no slider
                        for i in range(num_campos_servicos):
                            col_descricao, col_referencia = st.columns(2)
                            # Verifica se já existem registros de serviços cadastrados
                            if i < len(servicos_cadastrados):
                                registro = servicos_cadastrados[i]
                                with col_descricao:
                                    descricao = st.text_input(f"Descrição do Serviço {i + 1}", key=f"descricao_do_servico_{i}", value=registro.descricao).upper()
                                with col_referencia:
                                    referencia = st.text_input(f"Referência {i + 1}", key=f"referencia_{i}", value=registro.referencia).upper()
                            else:
                                # Se não houver registro suficiente, cria novos campos vazios
                                with col_descricao:
                                    descricao = st.text_input(f"Descrição do Serviço {i + 1}", key=f"descricao_do_servico_{i}").upper()
                                with col_referencia:
                                    referencia = st.text_input(f"Referência {i + 1}", key=f"referencia_{i}").upper()

                            # Armazena a descrição e referência se ambos estiverem preenchidos
                            if descricao and referencia:
                                producao[i + 1] = {'descricao': descricao, 'referencia': referencia}

                        # Gravação dos serviços
                        if st.button("Gravar Serviços"):
                            for i in range(num_campos_servicos):
                                # Verifica se estamos lidando com um serviço existente
                                if i < len(servicos_cadastrados):
                                    registro = servicos_cadastrados[i]
                                    # Atualiza o registro existente
                                    registro.descricao = producao[i + 1]['descricao']
                                    registro.referencia = producao[i + 1]['referencia']
                                    session.commit()
                                else:
                                    # Cria um novo serviço
                                    novo_servico = Servicos(
                                        descricao=producao[i + 1]['descricao'],
                                        referencia=producao[i + 1]['referencia'],
                                        item=i+1,
                                        diario_id=diario_selecionado_obj.id  # Atribui o ID do diário
                                    )
                                    session.add(novo_servico)
                                    session.commit()
                            # Confirma as alterações no banco de dados
                            st.success("Serviços gravados com sucesso!")

                    with tab_efetivo:

                        st.subheader("Efetivo Direto")
            
                        #contagem de quantas funções tem
                        contagem_funcoes_diretas = session.query(func.count(Efetivo_Direto.id)).filter(Efetivo_Direto.diario_id == diario_selecionado_obj.id).scalar()
                        
                        # slider para gerar os campos com as funções
                        num_campos_funcao_direta = st.slider("Quantas funções diretas", min_value=1, max_value=5, value=contagem_funcoes_diretas)

                        #funções já cadastradas
                        funcoes_diretas_cadastradas = session.query(Efetivo_Direto).filter_by(diario_id=diario_selecionado_obj.id).all()

                        #dicionário para guardas as funções preenchidas
                        efetivo_direto = {}

                        for i in range(num_campos_funcao_direta):
                            col_funcao, col_qtde, col_presente, col_ausente, col_efetivo = st.columns([2,1,1,1,1])

                            if i < len(funcoes_diretas_cadastradas):
                               
                                funcao_registrada = funcoes_diretas_cadastradas[i]

                                with col_funcao:
                                    funcao = st.text_input(f"Função {i+1}", key=f"funcao_{i}", value=funcao_registrada.funcao).upper()
                                with col_qtde:
                                    qtde = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1, value=funcao_registrada.qtde)
                                with col_presente:
                                    presente = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0, value=funcao_registrada.presente)
                                with col_ausente:
                                    ausente = st.number_input("Ausente", key=f"ausente_{i}", step=1, value=qtde-presente, disabled=True, min_value=0)
                                with col_efetivo:
                                    efetivo = st.number_input("Efetivo", disabled=True, key=f'efetivo_{i}', step=1, value=qtde-ausente)
                            else:
                                with col_funcao:
                                    funcao = st.text_input(f"Função {i+1}", key=f"funcao_{i}").upper()
                                with col_qtde:
                                    qtde = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1)
                                with col_presente:
                                    presente = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0)
                                with col_ausente:
                                    ausente = st.number_input("Ausente", key=f"ausente_{i}", step=1, value=qtde-presente, disabled=True, min_value=0)
                                with col_efetivo:
                                    efetivo = st.number_input("Efetivo", disabled=True, key=f'efetivo_{i}', step=1, value=qtde-ausente)
                           
                            if funcao and qtde:
                                efetivo_direto[funcao] = {
                                    'qtde': qtde, 
                                    'presente':presente,
                                    'ausente':ausente, 
                                    'efetivo':efetivo
                                    }

                        st.subheader("Efetivo Indireto")

                        #contagem de quantas funções tem
                        contagem_funcoes_indiretas = session.query(func.count(Efetivo_Indireto.id)).filter(Efetivo_Indireto.diario_id == diario_selecionado_obj.id).scalar()
                        
                        # slider para gerar os campos com as funções
                        num_campos_funcao_indireta = st.slider("Quantas funções indiretas", min_value=1, max_value=5, value=contagem_funcoes_indiretas)

                        #funções já cadastradas
                        funcoes_indiretas_cadastradas = session.query(Efetivo_Indireto).filter_by(diario_id=diario_selecionado_obj.id).all()

                        #dicionário para guardas as funções preenchidas
                        efetivo_indireto = {}

                        for i in range(num_campos_funcao_indireta):
                            col_funcao, col_efetivo = st.columns([2,1])
                            
                            if i < len(funcoes_indiretas_cadastradas):
                               
                                funcao_indireta_registrada = funcoes_indiretas_cadastradas[i]

                                with col_funcao:
                                    funcao =  st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}", value=funcao_indireta_registrada.funcao).upper()

                                with col_efetivo:
                                    efetivo = st.number_input("Efetivo", key=f'efetivo_indireto_{i}', step=1, value=funcao_indireta_registrada.efetivo)
                            else:
                                with col_funcao:
                                    funcao =  st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}").upper()

                                with col_efetivo:
                                    efetivo = st.number_input("Efetivo", key=f'efetivo_indireto_{i}', step=1)
                                
                            if funcao:
                                    efetivo_indireto[funcao] = efetivo
                         # Gravação dos serviços
                        if st.button("Gravar Efetivo", key="gravar_alteracoes_efetivo"):
                            for i in range(num_campos_funcao_direta):
                                # Verifica se estamos lidando com um serviço existente
                                if i < len(funcoes_diretas_cadastradas):
                                    funcao_direta_cadastrada = funcoes_diretas_cadastradas[i]
                                    
                                    # Atualiza o registro existente
                                    funcao_direta_cadastrada.funcao = list(efetivo_direto.keys())[i]  # Atualiza o nome da função
                                    funcao_direta_cadastrada.qtde = efetivo_direto[list(efetivo_direto.keys())[i]]['qtde']
                                    funcao_direta_cadastrada.presente = efetivo_direto[list(efetivo_direto.keys())[i]]['presente']
                                    funcao_direta_cadastrada.ausente = efetivo_direto[list(efetivo_direto.keys())[i]]['ausente']
                                    funcao_direta_cadastrada.efetivo = efetivo_direto[list(efetivo_direto.keys())[i]]['efetivo']
                                    session.commit()
                                else:
                                    # Cria um novo serviço
                                    nova_funcao = Efetivo_Direto(
                                        funcao=list(efetivo_direto.keys())[i],
                                        qtde=efetivo_direto[list(efetivo_direto.keys())[i]]['qtde'],
                                        presente=efetivo_direto[list(efetivo_direto.keys())[i]]['presente'],
                                        ausente=efetivo_direto[list(efetivo_direto.keys())[i]]['ausente'],
                                        efetivo=efetivo_direto[list(efetivo_direto.keys())[i]]['efetivo'],
                                        diario_id=diario_selecionado_obj.id  # Atribui o ID do diário
                                    )
                                    session.add(nova_funcao)
                                    session.commit()

                            # Confirma as alterações no banco de dados
                            st.success("Efetivo foi gravado com sucesso!")
                            
                    with tab_foto:

                        st.subheader("Adicionar Foto")

                        fotos_para_adicionar = st.file_uploader("Adicione as fotos", ["jpg", "jpeg", "png", "bmp"], True)

                        if st.button("Adicionar Fotos", key="add_mais_fotos"):
                            problema = False
                            
                            if not fotos_para_adicionar:
                                st.info("Não encontramos fotos para adicionar. Clique acima para adicionar as fotos que deseja")
                                problema = True
                            
                            if problema == False:
                                # Gravar as fotos
                
                                caminho_arquivos_salvos = salvar_fotos_na_pasta(diario_selecionado_obj.obra.contrato, diario_selecionado_obj.obra, diario_selecionado_obj, fotos_para_adicionar)

                                for caminho in caminho_arquivos_salvos:
                                    nova_foto = Foto(
                                        caminho_arquivo = caminho,
                                        diario_id = diario_selecionado_obj.id
                                        )
                                    session.add(nova_foto)
                                    session.commit()
                                    st.success(f"Foto(s) adicionadas com sucesso ao diario")

                        st.subheader("Remover Foto")
                        fotos_registradas = session.query(Foto).filter_by(diario_id=diario_selecionado_obj.id).all()
                        
                        for foto in fotos_registradas:

                            col_image, col_botao = st.columns([2,1], vertical_alignment="center",)

                            with col_image:
                                st.image(foto.caminho_arquivo, width=900)

                            with col_botao:
                                 if st.button("Remover esta foto", key=f"Apagar_foto_id{foto.id}"):
                                    apagar_foto(foto)

                else:
                    st.info("Nenhum diário encontrado para os critérios selecionados.")


            



        
        
        

        

