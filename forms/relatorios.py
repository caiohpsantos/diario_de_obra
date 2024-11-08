import os
import yaml
import streamlit as st
import calendar
from sqlalchemy import func, extract, asc
from time import sleep
from yaml import SafeLoader
from datetime import datetime, timedelta
from models import session, Contrato, Obra, Diario, Foto, Servicos, Efetivo_Direto, Efetivo_Indireto, Base



def relatorio_individual():
    # Formulário de Pesquisa para Edição de Diário
    st.title("Relatórios Mensais Individuais")

    st.subheader("Critérios de Pesquisa")

    diarios = None
    # Filtro de Contrato/Obra
    contratos = session.query(Contrato).filter_by(ativo=True).all()  # Obtém todos os contratos ativos
    contratos_opcoes = {contrato.nome: contrato.numero for contrato in contratos}
    contrato_selecionado = st.selectbox("Selecione o Contrato", options=[""] + list(contratos_opcoes.keys()))
    if contrato_selecionado:
        contrato_pro_relatorio = session.query(Contrato).filter_by(numero=contratos_opcoes[contrato_selecionado]).first()

    

        if contrato_selecionado:
            obras = session.query(Obra).filter_by(contrato_numero=contratos_opcoes[contrato_selecionado], ativo=True).all()
            obras_opcoes = {obra.nome: obra.id for obra in obras}
            obra_selecionada = st.selectbox("Selecione a Obra", options=[""] + list(obras_opcoes.keys()))
            if obra_selecionada:
                obra_pro_relatorio = session.query(Obra).filter_by(id=obras_opcoes[obra_selecionada]).first()

            st.divider()

            #Filtro de Mês e Ano
                
            if obra_selecionada:

                col_ano, col_mes = st.columns(2)

                with col_ano:
                    # Consulta para obter o ano mínimo e máximo de registros na tabela Diario para o par Contrato/Obra
                    ano_min = session.query(func.min(func.extract('year', Diario.data))).join(Obra).join(Contrato).filter(
                        Contrato.numero == contratos_opcoes[contrato_selecionado],
                        Obra.id == obras_opcoes[obra_selecionada]
                    ).scalar()
            
                    ano_max = session.query(func.max(func.extract('year', Diario.data))).join(Obra).join(Contrato).filter(
                        Contrato.numero == contratos_opcoes[contrato_selecionado],
                        Obra.id == obras_opcoes[obra_selecionada]
                    ).scalar()

                    if ano_min == ano_max:
                        anos_disponiveis = ano_min
                    
                    if ano_min < ano_max:
                        anos_disponiveis = list(range(ano_min, ano_max+1))
                    
                    ano_selecionado = st.selectbox("Escolha o ano", anos_disponiveis)

                with col_mes:
                    #Encontra o menor e o maior mês entre os diários registrados para o par Contrato/Obra
                    mes_min = session.query(func.min(func.extract('month', Diario.data))).join(Obra).join(Contrato).filter(
                        Contrato.numero == contratos_opcoes[contrato_selecionado],
                        Obra.id == obras_opcoes[obra_selecionada]
                    ).scalar()
            
                    mes_max = session.query(func.max(func.extract('month', Diario.data))).join(Obra).join(Contrato).filter(
                        Contrato.numero == contratos_opcoes[contrato_selecionado],
                        Obra.id == obras_opcoes[obra_selecionada]
                    ).scalar()

                    
                    meses_opcoes = {
                            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, 
                            "Junho": 6, "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, 
                            "Novembro": 11, "Dezembro": 12
                        }
                    
                    #Encontra mês anterior para setar o mês do selectbox
                    data_atual = datetime.now()
                    mes_anterior = (data_atual.replace(day=1) - timedelta(days=1)).month

                    mes_selecionado = st.selectbox("Selecione o Mês", list(meses_opcoes.keys()), index=mes_anterior-1)
                    mes_numero = meses_opcoes[mes_selecionado]

                
                # diarios = session.query(Diario).join(Obra).join(Contrato).filter(
                #     extract('month', Diario.data) == mes_numero,
                #     extract('year', Diario.data) == ano_selecionado,
                #     Contrato.numero == contrato_pro_relatorio.numero,     # Ou utilize Contrato.id caso esteja usando IDs
                #     Obra.id == obra_pro_relatorio.id              # Ou utilize Obra.id caso esteja usando IDs
                #     ).all()

                #construir data inicio
                data_inicio = datetime(ano_selecionado, mes_numero, contrato_pro_relatorio.dia_inicia_relatorio-1)
                
                #construir data final
                if contrato_pro_relatorio.dia_inicia_relatorio == 1 and contrato_pro_relatorio.dia_finaliza_relatorio == 30:
                    # Se a data de inicio for 1 e o final for 30, ainda está no mesmo mês, usa o código abaixo
                    ultimo_dia_mes = calendar.monthrange(ano_selecionado, mes_selecionado)[1]
                    data_fim = datetime(ano_selecionado, mes_selecionado, ultimo_dia_mes)
                
                # se for qualquer outra combinação, começa em um mês e termina em outra, usa o código abaixo
                else:

                    #Se o mês do relatório for Dezembro, muda pra o próximo ano e coloca o mês em Janeiro
                    if mes_numero == 12:
                        ano_fim = ano_selecionado + 1
                        mes_fim = 1
                    else:
                        #Caso o mês esteja entre Janeiro e Novembro mantém o mesmo ano e muda pra o próximo mês
                        ano_fim = ano_selecionado
                        mes_fim = mes_numero + 1
                
                data_fim = datetime(ano_fim, mes_fim, contrato_pro_relatorio.dia_finaliza_relatorio)
                
                #Monta a consulta com o contrato/obra selecionados e as datas montadas acima
                diarios = session.query(Diario).join(Obra).join(Contrato).filter(Contrato.numero == contrato_pro_relatorio.numero,
                                                        Obra.id == obra_pro_relatorio.id, 
                                                        Diario.data.between(data_inicio, data_fim)
                                                        ).order_by(asc(Diario.data)).all()
                
            st.divider()

            st.subheader("Diários localizados")
            if not diarios:
                st.info("Não encontramos diários de obra registrados para esse mês/ano dentro do contrato/obra selecionados")
            else:
                for diario in diarios:
                    with st.expander(f"{diario.data}"):
                        st.write(diario)


