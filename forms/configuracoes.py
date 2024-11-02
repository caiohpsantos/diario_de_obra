import os
import yaml
import streamlit as st
from yaml import SafeLoader

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
