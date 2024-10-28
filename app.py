import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from models import session
from forms import cadastros, diario

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

DIR_FOTOS = config['fotos_obras']

if not st.session_state['authentication_status']:
    authenticator.login()


if st.session_state['authentication_status']:
    with st.sidebar:
            st.write(f'Bem-vindo *{st.session_state["name"]}*')
            authenticator.logout()

            menu = option_menu("Menu Principal", ["Diário de Obra", "Cadastros", "Relatório"])

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

            