import os
import yaml
import streamlit as st
from yaml import SafeLoader
from models import session, Servicos_Padrao, Servicos


def armazenamento():
    
    '''carrega o arquivo de configuração'''
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    '''Gera um formulário e expõe os caminhos completos das pastas que recebem os arquivos de midia'''
    with st.form("caminho_fotos"):

        st.write("Informe o caminho da pasta que armazenará as fotos das vistorias")
        st.caption('''Caso altere a pasta, as fotos já salvas ficarão com o caminho de acesso inválido. Elas ainda vão existir na pasta antiga mas estarão inacessíveis pelo sistema.
         Caso necessário, é possível editar o diário, apagando o arquivo inválido e acrescentar o arquivo manualmente para salvar no novo caminho.''')
         
        pasta_fotos = st.text_input("Insira o caminho completo da pasta de fotos das vistorias", value=config['pasta_fotos'])

        gravar = st.form_submit_button("Gravar Alterações")

        '''Caso o usuário clique no botão Gravar começam os testes para validar os dados fornecidos
        Caso alguma validação dê errado a variável de controle 'problema' recebe True, o que impede que a gravaçao
        dos dados incorretos ocorra'''
        if gravar:
            problema = False

            '''verifica se as pastas existem e caso negativo retorna um erro informando e muda a 'problema' para verdadeiro'''
            if not os.path.exists(pasta_fotos):
                st.error("Caminho fornecido para a pasta de fotos é inválido. Verifique se foi digitado corretamente ou se as pastas existem")
                problema = True

            '''caso não haja problemas, inicia a atribuição dos novos valores à instancia do arquivo de configuração
            e salva logo depois'''
            if problema == False:
                config['pasta_fotos'] = pasta_fotos
                

                with open('config.yaml', 'w') as file:
                    config = yaml.dump(config, file, default_flow_style=False)
                
                st.success("Pastas de fotos foi alterada com sucesso.")

    # with st.form("caminho_backup"):
    #     st.write("Informe o caminho da pasta que armazenará o backup do banco de dados")
         
    #     pasta_backup = st.text_input("Insira o caminho completo da pasta de backup", value=config['pasta_backup'])

    #     gravar = st.form_submit_button("Gravar Alterações")

    #     '''Caso o usuário clique no botão Gravar começam os testes para validar os dados fornecidos
    #     Caso alguma validação dê errado a variável de controle 'problema' recebe True, o que impede que a gravaçao
    #     dos dados incorretos ocorra'''
    #     if gravar:
    #         problema = False

    #         '''verifica se as pastas existem e caso negativo retorna um erro informando e muda a 'problema' para verdadeiro'''
    #         if not os.path.exists(pasta_backup):
    #             st.error("Caminho fornecido para a pasta de backup é inválido. Verifique se foi digitado corretamente ou se as pastas existem")
    #             problema = True

    #         '''caso não haja problemas, inicia a atribuição dos novos valores à instancia do arquivo de configuração
    #         e salva logo depois'''
    #         if problema == False:
    #             config['pasta_backup'] = pasta_backup
                

    #             with open('config.yaml', 'w') as file:
    #                 config = yaml.dump(config, file, default_flow_style=False)
                
    #             st.success("Pastas de backup foi alterada com sucesso.")

def efetivo_padrao():

    # Carrega a configuração inicial do YAML
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    st.title("Efetivo padrão")
    st.caption("Insira aqui todas as funções diretas e indiretas que serão consideradas como padrão para o preenchimento do diário de obra.")

    with st.expander("Efetivo Direto"):

        # Carrega efetivo direto e conta registros
        efetivo_direto = config.get('efetivo_direto', {})
        num_registros_diretos = len(efetivo_direto)

        # Slider para definir o número de funções desejado
        qtde_funcoes_diretas_desejado = st.slider("Selecione quantas funções são necessárias", min_value=1, max_value=5, value=num_registros_diretos, step=1,
                                                    key='slider_funcoes_diretas')

        # Lista temporária para funções excluídas
        funcoes_diretas_removidas = []


        # Loop para exibir e modificar os campos das funções
        for i in range(qtde_funcoes_diretas_desejado):

            col_funcao, col_qtde, col_presente, col_ausente, col_efetivo, col_deletar = st.columns([2, 1, 1, 1, 1, 1])

            # Nome e dados da função atual ou novos campos vazios se excederem as funções cadastradas
            if i < num_registros_diretos:

                funcao_nome, funcao_dados = list(efetivo_direto.items())[i]
                with col_funcao:
                    funcao_direta = st.text_input(f"Função {i+1}", key=f"funcao_{i}", value=funcao_nome).upper()
                with col_qtde:
                    qtde_direta = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1, value=funcao_dados['qtde'])
                # Ajusta o valor de 'presente' para que ele não exceda o novo valor de 'qtde'
                if funcao_dados['presente'] > qtde_direta:
                    funcao_dados['presente'] = qtde_direta
                with col_presente:
                    presente_direto = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0, max_value=qtde_direta, value=funcao_dados['presente'])
                with col_ausente:
                    st.number_input("Ausente", key=f"ausente_{i}", min_value=0, max_value=qtde_direta, value=qtde_direta - presente_direto, step=1, disabled=True)
                with col_efetivo:
                    st.number_input("Efetivo", key=f"efetivo_{i}", min_value=0, max_value=qtde_direta, value=presente_direto, step=1, disabled=True)
            else:

                with col_funcao:
                    funcao_direta = st.text_input(f"Função {i+1}", key=f"funcao_{i}").upper()
                with col_qtde:
                    qtde_direta = st.number_input("Quantidade", key=f"qtde_{i}", step=1, min_value=1)
                with col_presente:
                    presente_direto = st.number_input("Presente", key=f"presente_{i}", step=1, min_value=0, max_value=qtde_direta)
                with col_ausente:
                    ausente = st.number_input("Ausente", key=f"ausente_{i}", min_value=0, max_value=qtde_direta, value=qtde_direta-presente_direto, step=1, disabled=True)
                with col_efetivo:
                    st.number_input("Efetivo", key=f"efetivo_{i}", min_value=0, max_value=qtde_direta, value=presente_direto, step=1, disabled=True)

            if st.checkbox(f"Remover Função Direta {funcao_direta}", key=f"remover_funcao_direta_{i}"):
                    funcoes_diretas_removidas.append(funcao_direta)

            # Atualiza o dicionário `efetivo_direto`
            if funcao_direta and qtde_direta > 0:
                efetivo_direto[funcao_direta] = {'qtde': qtde_direta, 'presente': presente_direto}

        # Remoção das funções listadas para exclusão
        for funcao_direta in funcoes_diretas_removidas:
            if funcao_direta in efetivo_direto:
                del efetivo_direto[funcao_direta]

    st.divider()

    with st.expander("Efetivo Indireto"):
        # Carrega efetivo indireto
        efetivo_indireto = config['efetivo_indireto']
        num_registros_indiretos = len(efetivo_indireto)

        # Slider para definir o número de funções desejado
        qtde_funcoes_indiretas_desejado = st.slider(
            "Selecione quantas funções são necessárias",
            min_value=1, max_value=5, value=num_registros_indiretos, step=1,
            key='slider_funcoes_indiretas'
        )

        # Lista temporária para funções excluídas
        funcoes_indiretas_removidas = []

        # Dicionário temporário para armazenar o efetivo indireto modificado
        efetivo_indireto_atualizado = {}

        # Loop para exibir e modificar os campos das funções
        for i in range(qtde_funcoes_indiretas_desejado):
            col_funcao, col_qtde, col_deletar = st.columns([2, 1, 1])

            # Nome e dados da função atual ou novos campos vazios se excederem as funções cadastradas
            if i < num_registros_indiretos:
                funcao_indireta_nome, funcao_indireta_dados = list(efetivo_indireto.items())[i]
                with col_funcao:
                    funcao_indireta = st.text_input(
                        f"Função {i+1}", key=f"funcao_indireta_{i}", value=funcao_indireta_nome
                    ).upper()

                with col_qtde:
                    qtde_indireta = st.number_input(
                        "Efetivo", key=f"qtde_indireta_{i}", step=1, value=funcao_indireta_dados['qtde']
                    )
            else:
                with col_funcao:
                    funcao_indireta = st.text_input(f"Função {i+1}", key=f"funcao_indireta_{i}").upper()

                with col_qtde:
                    qtde_indireta = st.number_input("Efetivo", key=f"qtde_indireta_{i}", step=1)

            if st.checkbox(f"Remover Função Indireta {funcao_indireta}", key=f"remover_funcao_indireta_{i}"):
                    funcoes_indiretas_removidas.append(funcao_indireta)

            # Atualiza o dicionário `efetivo_indireto_atualizado`
            if funcao_indireta and qtde_indireta > 0:
                efetivo_indireto_atualizado[funcao_indireta] = {'qtde': qtde_indireta}

        # Remoção das funções listadas para exclusão
        for funcao_removida in funcoes_indiretas_removidas:
            if funcao_removida in efetivo_indireto_atualizado:
                del efetivo_indireto_atualizado[funcao_removida]


    if st.button("Gravar Alterações"):
        # Salva as alterações no dicionário `config` e grava no arquivo YAML
        config['efetivo_direto'] = efetivo_direto
        config['efetivo_indireto'] = efetivo_indireto_atualizado  # usa o dicionário atualizado

        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

        st.success("Funções padrão foram alteradas com sucesso.")

def servicos_padrao():

    # Função para exibir a lista de serviços padrão e permitir a exclusão
    def listar_servicos_padrao():
        servicos = session.query(Servicos_Padrao).all()
        for index, servico in enumerate(servicos):
            col1, col2, col3 = st.columns([3,1,1], vertical_alignment="center", gap='large')
            with col1:
                novo_valor = st.text_input(f"Serviço {index + 1}", value=servico.descricao, key=f"servico_padrao_{servico.id}")
            with col2:
                if st.button("Alterar", key=f"alterar_{servico.id}"):
                    servico.descricao = novo_valor
                    session.commit()
                    st.success("Serviço alterado com sucesso!")
            with col3:
                desabilitar = False
                if session.query(Servicos).filter(Servicos.servicos_padrao_id == servico.id).first():
                    desabilitar = True
                if st.button("Remover", key=f"remover_{servico.id}", disabled=desabilitar, help="Caso não consiga clicar, significa que este serviço é referenciado em algum diário, portanto não pode ser apagado. Mas ainda pode editá-lo."):
                    session.delete(servico)
                    session.commit()
                    st.success("Serviço removido com sucesso!")
            st.divider()

    # Interface do Streamlit
    st.title("Cadastro de Serviços Padrão")

    with st.form("servico_padrao", clear_on_submit=True):
        # Entrada para adicionar novo serviço
        novo_servico = st.text_input("Digite o novo serviço").upper()

        # Botão para gravar o novo serviço
        if st.form_submit_button("Gravar"):
            if novo_servico.strip():
                # Cria e adiciona o novo serviço ao banco de dados
                servico = Servicos_Padrao(descricao=novo_servico)
                session.add(servico)
                session.commit()
                st.success("Serviço adicionado com sucesso!")
                
            else:
                st.error("O campo de serviço não pode estar vazio.")

    st.divider()  # Linha divisória

    # Lista de serviços cadastrados
    st.subheader("Serviços Cadastrados")
    st.divider()
    listar_servicos_padrao()

def versoes():
    st.title("Versões e correções")
    st.subheader('1.3')
    st.write('''
            **Cadastro de Diário:**\n
            * Há casos em que um diário pode ser registrado sem fotos. Há uma restrição que impede o registro do diário sem fotos.\n
            Corrigido, a restrição foi tirada e o diário pode ser registrado sem fotos.\n
            **Edição de Diário:**\n
            * A consulta que buscava os diários não carregava os relacionamentos das tabelas completamente, gerando erros. Corrigido, os relacionamentos\n
            entre as tabelas são carregados forçadamente junto com a consulta.
            * Ao editar um serviço que já existia em um diário já cadastrado, todos os serviços acabam ficando como o primeiro. Corrigido, agora cada serviço\n
            é salvo corretamente e tanto a edição quanto a adição de novos serviços funcionam corretamente.\n
            * Um diário agora pode ser registrado sem fotos. A tela da Edição de Diários foi atualizada para lidar com diários sem fotos.\n
            **Relatórios:**\n
            * A consulta que buscava os diários não carregava os relacionamentos das tabelas completamente, gerando erros na montagem do relatório pdf.\n
             Corrigido, os relacionamentos entre as tabelas são carregados forçadamente junto com a consulta.
            * Diários podem ser registrados sem fotos, a tela de Relatórios foi atualizada para lidar com esses diários sem fotos.\n
            **Relatório PDF:**
            * Atualizado para lidar com relatórios sem fotos. O campo observações mostrará a mensagem 'Este diário não possui fotos registradas' junto\n
            com quaisquer observações que o diário possua. Além disso, as assinaturas foram movidas para a primeira folha quando não hover fotos.\n 
            * Retirada a contagem de páginas.\n
            **Configurações:**\n
            * Qualquer serviço padrão podia ser excluído, caso algum serviço que está em uso por algum diário fosse excluído geraria um erro pela falta\n
            da referência. Já que a o diário apontaria para um serviço que não existe mais. Corrigido, caso um serviço padrão esteja registrado em algum diário,\n
            ele não poderá ser apagado. Uma mensagem aparecerá quando o usuário colocar o mouse sobre o botão especificando o motivo de não conseguir excluir.\n

            ''')
    st.subheader('1.2')
    st.write('''
            **Configurações:**\n
            * Criada a tela para registro/edição/exclusão dos serviços padrão. Facilitando o preenchimento do diário de obra com opções\n
             de serviço padronizados.\n
            **Cadastro/Edição de Diário:**\n
            * Telas de cadastro e edição do diário de obras agora abrem uma caixa de seleção para que o usário escolha qual serviço foi\n
            realizado no dia do registro. Ainda não é possível fazer registros enquanto grava o diário, Eles devem ser registrados no menu\n
            Configurações\Serviços Padrão.\n
            * Ao tentar editar um diário que já tinha sido incluído em um relatório o sistema negava a edição. Corrigido, como o diário pode\n
            passar batido com erros, bloquear a edição impede a correção. O impedimento foi retirado.
            * Imagens que representam o clima (limpo, nublado, chuvae impraticável) foram refeitas para incluir o nome do que simbolizam\n
            para contextualização mais fácil e rápida. Tanto na criação, edição, avaliação do diário.
            **Tela inicial:**\n
            * Inserido logo modificado da Rudra para personalização do programa.\n
            **Relatório PDF:**\n
            * Nos casos em que há muitos serviços e as descrições são muito longas os campos posteriores são jogados pra baixo,\n
            desfigurando o relatório. Corrigido, os campos de Produção tiveram suas linhas e tamanho da fonte reduzidas. Ocupando menos espaço.\n
            Além disso, o campo Observações foi bastante reduzido pois os textos que ele pode receber são pequenos.

            ''')
    st.subheader('1.1')
    st.write('''
            **Edição de Contratos:**\n
            * Contratos não poderiam ser apagados. Corrigido, contratos que não possuem obras e/ou diários\n
            atrelados a ele podem ser excluídos na tela de Edição de Contratos usando o expander que aparece logo acima. Caso haja alguma obra\diário\n
            atrelados ao contrato a exclusão já se torna impossível. Nesse caso ele pode ser desativado para não aparecer mais nos campos de\n
             registro de obras e diários.\n
            **Edição de Obras:**\n
            * Mensagem de desativação da Obra era a mesa da Ativação. Corrigidas e cada situação tem sua mensagem correspondente.\n
            * Obras não poderiam ser apagadas. Corrigido, obras que não possuem diários atrelados a elas\n
            podem ser excluídas na tela de Edição de Obras usando o expander que aparece logo acima. Caso haja algum diário\n
            atrelado à obra, a exclusão já se torna impossível. Nesse caso ela pode ser desativada para não aparecer mais nos campos de registro de diários.\n
            **Edição de Diários:**\n
            * Campos de datas estavam no formato americano. Corrigido, os campos apresentam datas no formato brasileiro.\n
            * Diários não poderiam ser apagados. Corrigido, Na tela de Edição de Diários, há uma aba de nome "Excluir". Basta seguir o processo de exclusão.\n
            **Relatório:**\n
            * Nomes de contrato longos acabam saindo do campo correspondente ou até da folha. Corrigido e nomes mais longos quebram \n
            a linha assim que chegam no limite do campo continuando logo abaixo.\n
            * O cabeçalho RELATÓRIO FOTOGRÁFICO que deve aparecer em cada página que possui fotos só aparecia na primeira página\n
            de fotos do diário. Corrigido, agora ele é gerado junto com cada página.\n
            * A marcação do clima da madrugada não acontecia, apesar de estar gravado no diário. Corrigido, agora o clima marcado \n
            para madrugada marca corretamente a posição.\n
            * Fotos dos diário não ficavam dimensionadas corretamente, tendo tamanhos diferentes e fora do padrão. Corrigido, agora \n
            as fotos são dimensionadas no registro ou edição do diário, padronizando a altura e largura. Dessa forma, haverão no máximo 6 fotos por folha.
            ''')
    st.subheader('1.0')
    st.write('''
                    Contratos: cadastrar, editar, ativar e desativar para não aceitar mais obras ou diários.\n
                    Obras: cadastrar, editar, ativar e desativar para não aceitar mais diários\n
                    Diários: cadastrar, editar, fotos são acrescentadas e carregadas\n
                    Efetivo Padrão: 2 opções de preenchimento, Padrão que é o que o mais comum ou digitar o efetivo para casos que o padrão não será usado.\n
                    Relatório: Gera um pdf com todos os campos do relatório original. Agregando todas as fotos.\n
                    Configurações: Permite alteração de senha do usuário, definir a pasta de armazenamento das fotos e alterar o Efetivo Padrão caso haja uma mudança que será recorrente.
                ''')