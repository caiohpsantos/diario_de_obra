import os
import yaml
import streamlit as st
from time import sleep
from yaml import SafeLoader
from datetime import datetime, timedelta
from models import session, Contrato, Obra, Diario, Foto, Servicos, Efetivo_Direto, Efetivo_Indireto, Servicos_Padrao, Base
from .funcionalidades import salvar_fotos_na_pasta, apagar_foto, apagar_servico, apagar_funcao, apagar_fotos_na_pasta, apagar_diario
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload


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

        #Trata das datas e climas
        st.subheader("Data")

        data = st.date_input("Data", format="DD/MM/YYYY", value=datetime.today(),label_visibility='hidden')

        if data:
            
            if session.query(Diario).filter_by(obra_id=obra_do_diario.id, data=data).first():
                st.error(f"Já existe um diário registrado para esse contrato/obra no dia {data.strftime("%d/%m/%Y")}. Você pode editá-lo no menu Editar Diário, logo acima.")
            
            else:
        
                st.divider()

                st.subheader("Turno/Tempo")

                col_manha,col_tarde,col_noite, col_madrugada = st.columns(4)
                
                opcoes_clima = ["Limpo", "Nublado", "Chuva", "Impraticável"]

                with col_manha:
                    clima_manha = st.radio("**CLIMA DA MANHÃ**", opcoes_clima)

                with col_tarde:
                    clima_tarde = st.radio("**CLIMA DA TARDE**", opcoes_clima)

                with col_noite:
                    clima_noite = st.radio("**CLIMA DA NOITE**", opcoes_clima)

                with col_madrugada:
                    clima_madrugada = st.radio("**CLIMA DA MADRUGADA**", opcoes_clima)

                st.divider()
                # Trata dos serviços feitos
                st.subheader("Produção Diária")

                producao = {}

                num_campos_servicos = st.slider("Quantos serviços foram feitos", min_value=1, max_value=14, value=1)

                
                # Carrega as opções de serviços em um dicionário {descricao: id}
                opcoes_servicos = {servico.descricao: servico.id for servico in session.query(Servicos_Padrao).order_by(Servicos_Padrao.descricao).all()}

                # Adiciona uma opção vazia para o selectbox
                opcoes_servicos = {'': None, **opcoes_servicos}

                col_servico, col_descricao = st.columns(2)
                for i in range(num_campos_servicos):
                    with col_servico:
                        # Selectbox que exibe a descrição, mas retorna o id do serviço selecionado
                        servico_selecionado = st.selectbox(f"Descrição do Serviço {i + 1}", options=list(opcoes_servicos.keys()), key=f"descricao_do_servico_{i}")
                        servico_selecionado_id = opcoes_servicos[servico_selecionado]  # Obtém o id do serviço selecionado

                    with col_descricao:
                        referencia = st.text_input(f"Referência {i + 1}", key=f"referencia_{i}").upper().strip()

                    if servico_selecionado_id and referencia:
                        producao[i + 1] = {'servico_selecionado_id': servico_selecionado_id, 'referencia': referencia}


                st.divider()
                # Trata da mão-de-obra que foi alocada para esse contrato/obra/dia
                st.subheader("Efetivo Alocado")

                efetivo_direto = {}
                efetivo_indireto = {}

                efetivo_padrao = st.radio("Usar efetivo padrão", ["Sim", "Digitar Efetivo"], horizontal=True)
                erro_presente = []
                if efetivo_padrao == "Sim":
                    # Carrega a configuração inicial do YAML
                    with open('config.yaml') as file:
                        config = yaml.load(file, Loader=SafeLoader)

                    efetivo_direto = config['efetivo_direto']
                    
                    efetivo_indireto = config['efetivo_indireto']

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
                            funcao = st.text_input(f"Função {i+1}", key=f"funcao_{i}").upper().strip()
                        with col_qtde:
                            qtde = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1)
                        with col_presente:
                            presente = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0)
                        # Compara se o presente é maior que a qtde, caso seja mostra uma mensagem de erro e acrescenta
                        # o número da função numa lista para ser exibida após clicar no botão Gravar caso o usuário continue sem a correção
                        if qtde < presente:
                            st.error(f"Função {i+1}: Há mais pessoas presentes do que a quantidade total de pessoas.")
                            erro_presente.append(i + 1)
                        with col_ausente:
                            ausente = st.number_input("Ausente", key=f"ausente_{i}", step=1, value=qtde-presente, disabled=True)
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
                # Trata de observações diversas que não estão previstas no relatório
                st.subheader("Observações")

                observacoes = st.text_area("Digite as observações").upper().strip()

                st.divider()
                # Trata das fotos que devem ser anexadas ao diário
                st.subheader("Registro Fotográfico")

                fotos = st.file_uploader("Adicione as fotos", ["jpg", "jpeg", "png", "bmp"], True)

                gravar = st.button("Gravar")

                #Inicia a gravação
                if gravar:

                    problema = False
                    #Verifica se todos os campos foram preenchidos
                    if not producao:
                        st.error("Não há nenhum serviço preenchido")
                        problema = True

                    #Verifica se a opção para digitar a mão-de-obra está ativa e se há valores digitados
                    if efetivo_padrao == "Digitar Efetivo" and (efetivo_direto == {} or efetivo_indireto == {}):
                        st.error("Foi escolhida a opção de digitar o efetivo alocado, porém não foram registradas nenhuma função ou quantidade de pessoas.")
                        problema = True
                    
                    #Verifica se a qtde de pessoas em determinada função é menor que os presentes
                    if erro_presente:
                        st.error(f"Corrija as funções com quantidade incorreta: {', '.join(map(str, erro_presente))}")
                        problema = True

                    #Verificas e já há um diário cadastrado para a dupla contrato/obra no dia preenchido
                    if session.query(Diario).filter_by(obra_id = obra_do_diario.id, data=data).first() is not None:
                        st.error(f"Já existe um diário gravado para este contrato/obra no dia {data.strftime("%d/%m/%Y")}")
                        problema = True
                    
                    #Caso não tenha nenhum problema inicia a gravação do diário por partes
                    if problema == False:

                        # Gravar o diário
                        novo_diario = Diario(
                            data=data, 
                            clima_manha=clima_manha, 
                            clima_tarde=clima_tarde, 
                            clima_noite=clima_noite,
                            clima_madrugada=clima_madrugada,
                            observacoes=observacoes, 
                            obra_id = obra_do_diario.id,
                            usuario_criador=st.session_state['name'])
                        session.add(novo_diario)
                        session.commit()
                        continuar = True

                        # Gravar as fotos
                        if continuar == True and fotos:
                            try:
                                caminho_arquivos_salvos = salvar_fotos_na_pasta(contrato_do_diario, obra_do_diario, novo_diario, fotos)
                                for caminho in caminho_arquivos_salvos:
                                    nova_foto = Foto(
                                        caminho_arquivo = caminho,
                                        diario_id = novo_diario.id
                                        )
                                    session.add(nova_foto)
                                    session.commit()
                                    continuar = True
                            except:
                                session.delete(novo_diario)
                                apagar_fotos_na_pasta(caminho_arquivos_salvos)
                                continuar = False
                                st.error(f"Houve um erro e não foi possível salvar as fotos deste diário. A operação foi cancelada. Caso o erro persista, entre em contato com o suporte.")
                        
                        # Gravar os serviços
                        if continuar == True:
                            try:
                                for item, dados_servico in producao.items():
                                    novo_servico = Servicos(
                                        servicos_padrao_id = dados_servico['servico_selecionado_id'], 
                                        item=item, 
                                        referencia=dados_servico['referencia'], 
                                        diario_id=novo_diario.id)
                                    session.add(novo_servico)
                                    session.commit()
                            except:
                                for foto in session.query(fotos).filter_by(novo_diario.id).all():
                                    apagar_fotos_na_pasta(foto.caminho_arquivo)
                                    session.delete(foto)
                                session.delete(novo_diario)
                                continuar = False
                                st.error("Não foi possível gravar os serviços selecionados para o novo diário. A operação foi cancelada. Caso o erro persista, entre em contato com o suporte.")
                        
                        
                        # Gravar a mão-de-obra separada em efetivos diretos e indiretos
                        if continuar == True:
                            try:
                                for funcao, dados in efetivo_direto.items():
                                    novo_efetivo_direto = Efetivo_Direto(
                                        funcao=funcao,
                                        qtde=dados['qtde'],
                                        presente=dados['presente'],
                                        diario_id=novo_diario.id
                                    )
                                    session.add(novo_efetivo_direto)
                                    session.commit()
                            except:
                                for servico in session.query(Servicos).filter_by(novo_diario.id).all():
                                    session.delete(servico)
                                for foto in session.query(fotos).filter_by(novo_diario.id).all():
                                    apagar_fotos_na_pasta(foto.caminho_arquivo)
                                    session.delete(foto)
                                session.delete(novo_diario)
                                continuar = False
                                st.error("Não foi possível gravar o efetivo direto selecionado para o novo diário. A operação foi cancelada. Caso o erro persista, entre em contato com o suporte.")

                        
                        if continuar == True:
                            try:
                                for funcao, dados in efetivo_indireto.items():
                                    
                                    novo_efetivo_indireto = Efetivo_Indireto(
                                        funcao=funcao,
                                        efetivo=dados['qtde'],
                                        diario_id = novo_diario.id
                                    )
                                    session.add(novo_efetivo_indireto)
                                    session.commit()
                            except:
                                for funcao_direta in session.query(Efetivo_Direto).filter_by(novo_diario.id).all():
                                    session.delete(funcao_direta)
                                for servico in session.query(Servicos).filter_by(novo_diario.id).all():
                                    session.delete(servico)
                                for foto in session.query(fotos).filter_by(novo_diario.id).all():
                                    apagar_fotos_na_pasta(foto.caminho_arquivo)
                                    session.delete(foto)
                                session.delete(novo_diario)
                                continuar = False
                                st.error("Não foi possível gravar o efetivo indireto selecionado para o novo diário. A operação foi cancelada. Caso o erro persista, entre em contato com o suporte.")
                                
                        
                            st.success("Diário de Obra gravado com sucesso")

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
            data_inicio = st.date_input("Data Inicial (opcional)", value=datetime.today() - timedelta(days=7), format="DD/MM/YYYY")
        with col2:
            data_fim = st.date_input("Data Final (opcional)", value=datetime.today(), format="DD/MM/YYYY")

      
        # Verifica o intervalo de datas válido, caso as datas sejam informadas
        if data_inicio > data_fim:
            st.error("A data inicial deve ser anterior ou igual à data final.")
        else:
            
            query = session.query(Diario).join(Diario.obra).join(Obra.contrato).options(
                        joinedload(Diario.obra).joinedload(Obra.contrato)  # Carrega obra e contrato associados
                    )

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

            # Executa a consulta
            diarios_resultados = query.all()
           
            # Exibe os resultados
            if diarios_resultados:
                
                diario_opcoes = {
                                    f"{d.data.strftime('%d/%m/%Y')} - {d.obra.contrato.nome} - {d.obra.nome} - DIÁRIO {d.id}": d
                                    for d in diarios_resultados
                                    if d.obra and d.obra.contrato
                                }
                diario_selecionado = st.radio("Selecione um Diário:", list(diario_opcoes.keys()), index=None)
                if diario_selecionado:
                    diario_selecionado_obj = diario_opcoes[diario_selecionado]
                    # Gera as abas para edição quando há um diario_selecionado no radio                
                    tab_tempo, tab_producao, tab_efetivo, tab_foto, tab_exclusao = st.tabs(["Data/Tempo", "Produção", "Efetivo", "Fotos", "Excluir"])
                    
                    st.caption(f"Criado por {diario_selecionado_obj.usuario_criador} em {diario_selecionado_obj.created_at.strftime('%d/%m/%Y %H:%M:%S')}")


                    #Para melhor visualização, separa o diário em 4 abas temáticas

                    #Aba que trata de data e condições climáticas
                    with tab_tempo:
                        st.subheader("Data")

                        data = st.date_input("Data", format="DD/MM/YYYY", value=diario_selecionado_obj.data,label_visibility='hidden')

                        st.divider()

                        st.subheader("Turno/Tempo")

                        col_manha,col_tarde,col_noite, col_madrugada = st.columns(4)
                        
                        opcoes_clima = ["Limpo", "Nublado", "Chuva", "Impraticável"]

                        with col_manha:
                            clima_manha = st.radio("**CLIMA DA MANHÃ**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_manha))

                        with col_tarde:
                            clima_tarde = st.radio("**CLIMA DA TARDE**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_tarde))

                        with col_noite:
                            clima_noite = st.radio("**CLIMA DA NOITE**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_noite))
                        
                        with col_madrugada:
                            clima_madrugada = st.radio("**CLIMA DA MADRUGADA**", opcoes_clima, index=opcoes_clima.index(diario_selecionado_obj.clima_madrugada))

                        gravar = st.button("Gravar Alterações", help="Apenas as informações dessa aba serão alteradas")

                        if gravar:

                            problema = False
                            
                            #Verifica se os campos possuem valores diferentes dos registros originais
                            campos_alterados = (
                                diario_selecionado_obj.data != data or
                                diario_selecionado_obj.clima_manha != clima_manha or
                                diario_selecionado_obj.clima_tarde != clima_tarde or
                                diario_selecionado_obj.clima_noite != clima_noite or
                                diario_selecionado_obj.clima_madrugada != clima_madrugada
                            )

                            #Caso algum campo tenha sido alterado começa as verificações de erros
                            if campos_alterados:
                                #Verifica se a data está vazia
                                if not data:
                                    st.error("O campo data não pode ficar vazio")
                                    problema = True

                                #Não encontrando problema inicia a atualização dos dados
                                if not problema:
                                    diario_selecionado_obj.data = data
                                    diario_selecionado_obj.clima_manha = clima_manha
                                    diario_selecionado_obj.clima_tarde = clima_tarde
                                    diario_selecionado_obj.clima_noite = clima_noite
                                    diario_selecionado_obj.clima_madrugada = clima_madrugada
                                    session.commit()
                                    st.success(f"Os dados de Tempo/Turno do diário nº {diario_selecionado_obj.id} do contrato {diario_selecionado_obj.obra.contrato.nome} obra {diario_selecionado_obj.obra.nome} foram alterados com sucesso.")
                            
                            else:
                                st.info("Nenhuma alteração foi detectada")

                    #Aba que trada dos serviços executados               
                    with tab_producao:
                        st.subheader("Produção Diária")

                        # Contagem atual de serviços para definir o valor inicial do slider
                        contagem_servicos = session.query(func.count(Servicos.id)).filter(Servicos.diario_id == diario_selecionado_obj.id).scalar()

                        # Slider para selecionar o número de serviços
                        num_campos_servicos = st.slider("Quantos serviços foram feitos", min_value=1, max_value=14, value=contagem_servicos)

                        # Obtém os serviços cadastrados no diário
                        servicos_cadastrados_diario = session.query(Servicos).filter_by(diario_id=diario_selecionado_obj.id).all()

                        # Dicionário para armazenar a produção
                        producao = {}

                        # Consulta todos os serviços padrão para montar as opções do selectbox
                        opcoes_servicos = {servico.descricao: servico.id for servico in session.query(Servicos_Padrao).order_by(Servicos_Padrao.descricao).all()}

                        # Cria campos de entrada de acordo com o número selecionado no slider
                        for i in range(num_campos_servicos):
                            col_servico_padrao, col_referencia, col_deletar = st.columns([2, 2, 1], vertical_alignment="center")

                            # Variáveis para armazenar dados do serviço atual
                            servico_selecionado_id = None
                            referencia = None

                            # Verifica se já existem registros de serviços cadastrados
                            if i < len(servicos_cadastrados_diario):
                                registro = servicos_cadastrados_diario[i]
                                with col_servico_padrao:
                                    # Obtém o id do serviço padrão cadastrado
                                    servico_padrao_id = registro.servicos_padrao_id

                                    # Localiza a descrição correspondente ao ID cadastrado
                                    descricao_servico_padrao = [desc for desc, id in opcoes_servicos.items() if id == servico_padrao_id][0]

                                    # Define o índice da descrição selecionada no selectbox
                                    index_servico = list(opcoes_servicos.keys()).index(descricao_servico_padrao)

                                    # Exibe o selectbox com o índice da opção correta
                                    servico_selecionado = st.selectbox(
                                        f"Descrição do Serviço {i + 1} (Cadastrado)",
                                        options=list(opcoes_servicos.keys()),
                                        key=f"descricao_do_servico_existente_{i+1}",
                                        index=index_servico
                                    )
                                    servico_selecionado_id = opcoes_servicos[servico_selecionado]

                                with col_referencia:
                                    referencia = st.text_input(
                                        f"Referência {i + 1} (Cadastrado)",
                                        key=f"referencia_cadastrada_{i+1}",
                                        value=registro.referencia
                                    ).upper()

                                with col_deletar:
                                    if st.button("Deletar este Serviço", key=f"deletar_funcao_{registro.id}"):
                                        apagar_servico(registro)

                            else:
                                # Se não houver registro suficiente, cria novos campos vazios
                                with col_servico_padrao:
                                    servico_selecionado = st.selectbox(
                                        f"Descrição do Serviço {i + 1} (Novo)",
                                        options=list(opcoes_servicos.keys()),
                                        key=f"descricao_do_servico_novo_{i+1}"
                                    )
                                    servico_selecionado_id = opcoes_servicos[servico_selecionado]

                                with col_referencia:
                                    referencia = st.text_input(
                                        f"Referência {i + 1} (Nova)",
                                        key=f"referencia_nova_{i+1}"
                                    ).upper()

                            # Armazena a descrição e referência no dicionário `producao`
                            if servico_selecionado_id and referencia:
                                producao[i + 1] = {'servico_padrao_id': servico_selecionado_id, 'referencia': referencia}

                        # Gravação dos serviços
                        if st.button("Gravar Serviços"):
                            problema = False

                            if not producao:
                                st.error("É necessário pelo menos 1 serviço para cada diário. Preencha algum no campo acima.")
                                problema = True

                            if problema == False:
                                for i in range(num_campos_servicos):
                                    # Verifica se estamos lidando com um serviço existente
                                    if i < len(servicos_cadastrados_diario):
                                        registro = servicos_cadastrados_diario[i]
                                        # Atualiza o registro existente
                                        registro.servicos_padrao_id = producao[i + 1]['servico_padrao_id']
                                        registro.referencia = producao[i + 1]['referencia']
                                        session.commit()
                                    else:
                                        # Cria um novo serviço
                                        novo_servico = Servicos(
                                            servicos_padrao_id=producao[i + 1]['servico_padrao_id'],
                                            referencia=producao[i + 1]['referencia'],
                                            item=i+1,
                                            diario_id=diario_selecionado_obj.id  # Atribui o ID do diário
                                        )
                                        session.add(novo_servico)
                                        session.commit()

                                # Confirma as alterações no banco de dados
                                st.success("Serviços gravados com sucesso!")


                    #Aba que trata da mão de obra alocada
                    with tab_efetivo:

                        with st.expander("Efetivo Direto"):
            
                            #contagem de quantas funções tem
                            contagem_funcoes_diretas = session.query(func.count(Efetivo_Direto.id)).filter(Efetivo_Direto.diario_id == diario_selecionado_obj.id).scalar()
                            
                            # slider para gerar os campos com as funções
                            num_campos_funcao_direta = st.slider("Quantas funções diretas", min_value=1, max_value=5, value=contagem_funcoes_diretas)

                            #funções já cadastradas
                            funcoes_diretas_cadastradas = session.query(Efetivo_Direto).filter_by(diario_id=diario_selecionado_obj.id).all()

                            #dicionário para guardas as funções preenchidas
                            efetivo_direto = {}

                            for i in range(num_campos_funcao_direta):
                                col_funcao, col_qtde, col_presente, col_ausente, col_efetivo, col_deletar = st.columns([2,1,1,1,1,1], vertical_alignment="center")

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
                                    with col_deletar:
                                        if st.button("Remover Função", key=f"remover_funcao_{i}"):
                                            apagar_funcao(funcao_registrada)

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

                        with st.expander("Efetivo Indireto"):

                            #contagem de quantas funções tem
                            contagem_funcoes_indiretas = session.query(func.count(Efetivo_Indireto.id)).filter(Efetivo_Indireto.diario_id == diario_selecionado_obj.id).scalar()
                            
                            # slider para gerar os campos com as funções
                            num_campos_funcao_indireta = st.slider("Quantas funções indiretas", min_value=1, max_value=5, value=contagem_funcoes_indiretas)

                            #funções já cadastradas
                            funcoes_indiretas_cadastradas = session.query(Efetivo_Indireto).filter_by(diario_id=diario_selecionado_obj.id).all()

                            #dicionário para guardas as funções preenchidas
                            efetivo_indireto = {}

                            for i in range(num_campos_funcao_indireta):
                                col_funcao, col_efetivo, col_deletar = st.columns([2,1,1], vertical_alignment="center")
                                
                                if i < len(funcoes_indiretas_cadastradas):
                                
                                    funcao_indireta_registrada = funcoes_indiretas_cadastradas[i]

                                    with col_funcao:
                                        funcao =  st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}", value=funcao_indireta_registrada.funcao).upper()

                                    with col_efetivo:
                                        efetivo = st.number_input("Efetivo", key=f'efetivo_indireto_{i}', step=1, value=funcao_indireta_registrada.efetivo)
                                    
                                    with col_deletar:
                                        if st.button("Remover Função", key=f"remover_funcao_indireta_{i}"):
                                            apagar_funcao(funcao_indireta_registrada)
                                else:
                                    with col_funcao:
                                        funcao =  st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}").upper()

                                    with col_efetivo:
                                        efetivo = st.number_input("Efetivo", key=f'efetivo_indireto_{i}', step=1)

                                    
                                if funcao:
                                        efetivo_indireto[funcao] = efetivo
                         # Gravação dos serviços
                        if st.button("Gravar Efetivo", key="gravar_alteracoes_efetivo"):
                            problema = False

                            if not efetivo_direto:
                                st.error("Não há funções diretas cadastradas. Elas são obrigatórias. O Cadastro é feito no menu Efetivo Direto, logo acima.")
                                problema = True

                            if not efetivo_indireto:
                                st.error("Não há funções indiretas cadastradas. Elas são obrigatórias. O Cadastro é feito no menu Efetivo Indireto, logo acima.")
                                problema = True
                            
                            if problema == False:
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

                    #Aba que trata das fotos (inclusão e remoção)    
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

                                try:
                                    for caminho in caminho_arquivos_salvos:
                                        nova_foto = Foto(
                                            caminho_arquivo = caminho,
                                            diario_id = diario_selecionado_obj.id
                                            )
                                        session.add(nova_foto)
                                        session.commit()
                                    st.success(f"Foto(s) adicionadas com sucesso ao diario")
                                except:
                                    st.error(f"Houve um erro ao gravar as fotos para o diario {diario_selecionado_obj}. Comunique o suporte no menu direito superior, em Report a Bug")

                        st.subheader("Remover Foto")
                        fotos_registradas = session.query(Foto).filter_by(diario_id=diario_selecionado_obj.id).all()
                        
                        if fotos_registradas:
                            for foto in fotos_registradas:

                                col_image, col_botao = st.columns([2,1], vertical_alignment="center",)

                                with col_image:
                                    st.image(foto.caminho_arquivo, width=900)

                                with col_botao:
                                 if st.button("Remover esta foto", key=f"Apagar_foto_id{foto.id}"):
                                    apagar_foto(foto)

                        else:
                            st.info("Não há fotos registradas para esse diário")
                    #Aba que trata da exclusão do diário
                    with tab_exclusao:
                        
                            st.subheader("Excluir Diário")
                            st.write("Para excluir esse diário, clique no botão abaixo")
                            if st.button("Excluir", key=f"excluir_diario_{diario_selecionado_obj.id}"):
                                apagar_diario(diario_selecionado_obj)
                        
            else:
                    st.info("Nenhum diário encontrado para os critérios selecionados.")


            



        
        
        

        

