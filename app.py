import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from models import session
from forms import cadastros, diario, configuracoes

st.set_page_config(layout="wide")

st.header("Sistema Gerenciamento Diário de Obras")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

if not st.session_state['authentication_status']:
    authenticator.login()


if st.session_state['authentication_status']:
    with st.sidebar:
            st.write(f'Bem-vindo *{st.session_state["name"]}*')
            authenticator.logout()

            menu = option_menu("Menu Principal", ["Diário de Obra", "Cadastros", "Relatório", "Configurações"])

    match menu:

        case "Cadastros":
            
            menu_secundario = option_menu("Cadastrar", ["Novo Contrato", "Editar Contrato", "Nova Obra", "Editar Obra"], orientation="horizontal")

            match menu_secundario:
                case "Novo Contrato":
                    cadastros.cad_contrato()
                
                case "Editar Contrato":
                    cadastros.edit_contrato()

                case "Nova Obra":
                    cadastros.cad_obra()

                case "Editar Obra":
                    cadastros.edit_obra()
        
        case "Diário de Obra":

            menu_secundario = option_menu("Diário de Obra", ["Novo Diário", "Editar Diário"], orientation="horizontal")

            match menu_secundario:

                case "Novo Diário":
                    diario.novo_diario()

        case "Configurações":

            menu_secundario = option_menu("Configurações", ["Alterar Senha", "Armazenamento Fotos"], orientation="horizontal")

            match menu_secundario:

                case "Alterar Senha":
                    if st.session_state['authentication_status']:
                        try:
                            if authenticator.reset_password(st.session_state['username'],fields={
                                'Form name':f'Trocar a senha de {st.session_state["name"]}',
                                'Current password':'Senha atual',
                                'New password':'Senha nova',
                                'Repeat password': 'Repita a senha nova',
                                'Reset':'Confirmar'
                            }):
                                with open('config.yaml', 'w') as file:
                                    yaml.dump(config, file, default_flow_style=False)
                                st.success('Senha alterada com sucesso')
                        except Exception as e:
                            st.error(e)
                    elif st.session_state['authentication_status'] is False:
                        st.error('Usuário ou senha incorreta. Tente novamente')
                    elif st.session_state['authentication_status'] is None:
                        st.warning('Faça o login para acessar o sistema')

                case "Armazenamento Fotos":
                    configuracoes.caminho_fotos()