import streamlit as st
from models import session, Contrato, Obra, Diario, Foto, Base

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
        