import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from PIL import Image as PILImage


def reset_all_states():
    """Função para reiniciar todos os estados da sessão"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.step = 1


def criar_pdf(operation, observation, uploaded_files):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("Controle de Documentos", title_style))
    
    # Informações da operação
    operation_text = f"Operação: {operation}"
    if observation:
        operation_text += f"\nObservação: {observation}"
    story.append(Paragraph(operation_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # Data e hora
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    story.append(Paragraph(f"Data/Hora: {current_time}", styles['Normal']))
    story.append(Spacer(1, 30))

    # Adicionar documentos
    for uploaded_file in uploaded_files:
        # Adicionar nome do arquivo
        story.append(Paragraph(f"Documento: {uploaded_file.name}", styles['Heading2']))
        
        try:
            # Tentar abrir como imagem
            image_buffer = io.BytesIO(uploaded_file.getvalue())
            img = PILImage.open(image_buffer)
            
            # Converter para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Salvar em um novo buffer
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            # Adicionar imagem ao PDF
            img_width = 6 * inch  # largura máxima
            img_height = img_width * img.size[1] / img.size[0]  # manter proporção
            story.append(Image(img_buffer, width=img_width, height=img_height))
            
        except Exception as e:
            # Se não for imagem, adicionar mensagem
            story.append(Paragraph(f"Conteúdo não visualizável: {uploaded_file.type}", styles['Normal']))
        
        story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)
    return buffer

def enviar_email(pdf_buffer, operation, observation=""):
    remetente = "cadastrotmt@gmail.com"
    senha = "qptm rgbz dzpr wdhk"
    destinatario = "beatriz.campos@tmtlog.com" 

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    
    # Assunto do email com o nome da operação
    assunto = f"CONTROLE DE DOCUMENTOS - {operation}"
    if observation:
        assunto += f" - {observation}"
    msg['Subject'] = assunto

    # Corpo do email
    corpo_email = "Segue em anexo os documentos."
    msg.attach(MIMEText(corpo_email, 'plain'))

    # Anexar PDF
    pdf_attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype='pdf')
    pdf_attachment.add_header('Content-Disposition', 'attachment', 
                            filename=f'controle_documentos_{operation}.pdf')
    msg.attach(pdf_attachment)

    # Enviar email
    servidor_smtp = smtplib.SMTP('smtp.gmail.com', 587)
    servidor_smtp.starttls()
    servidor_smtp.login(remetente, senha)
    servidor_smtp.send_message(msg)
    servidor_smtp.quit()

def main():
    st.title("Controle de Documentos")
    
    # Inicialização das variáveis de sessão
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'operation' not in st.session_state:
        st.session_state.operation = ""
    if 'observation' not in st.session_state:
        st.session_state.observation = ""
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False
        
    # Passo 1: Seleção da operação
    if st.session_state.step == 1:
        st.header("1º Passo: Selecionar Operação")
        
        operations = [
            "DSM",
            "CRS",
            "MULTITÉCNICA",
            "LEROY",
            "QUIMEX",
            "CIMENTO NACIONAL",
            "NESTLÉ",
            "OUTROS"
        ]
        
        operation = st.selectbox("Selecione a operação:", operations, key='operation_select')
        
        observation = ""
        if operation == "OUTROS":
            observation = st.text_input("Digite o nome da operação:", key='observation_input')
            if not observation:
                st.warning("Por favor, digite o nome da operação.")
                return
                
        if st.button("Próximo"):
            st.session_state.operation = operation
            st.session_state.observation = observation
            st.session_state.step = 2
            st.rerun()
            
    # Passo 2: Verificação do documento
    elif st.session_state.step == 2:
        st.header("2º Passo: Verificação do Documento")
        
        doc_signed = st.checkbox("O documento está assinado?", key='doc_signed')
        doc_dated = st.checkbox("O documento está datado?", key='doc_dated')
        all_attachments = st.checkbox("Todos os comprovantes relacionados à carga estão em anexo?", key='all_attachments')
        
        if st.button("Voltar"):
            st.session_state.step = 1
            st.rerun()
            
        if st.button("Próximo"):
            if not (doc_signed and doc_dated and all_attachments):
                st.error("Todos os itens devem ser confirmados antes de prosseguir.")
                return
                
            st.session_state.step = 3
            st.rerun()
            
    # Passo 3: Upload e envio
    elif st.session_state.step == 3:
        st.header("3º Passo: Anexar e Enviar Documentos")
        
        uploaded_files = st.file_uploader(
            "Selecione o(s) documento(s):",
            accept_multiple_files=True,
            type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
            key='file_uploader'
        )
        
        if st.button("Voltar"):
            st.session_state.step = 2
            st.rerun()
            
        if st.button("Enviar"):
            if not uploaded_files:
                st.error("Por favor, anexe pelo menos um documento.")
                return
            
            try:
                with st.spinner("Processando documentos e enviando email..."):
                    # Criar PDF
                    pdf_buffer = criar_pdf(
                        st.session_state.operation,
                        st.session_state.observation,
                        uploaded_files
                    )
                    
                    # Enviar email
                    enviar_email(
                        pdf_buffer,
                        st.session_state.operation,
                        st.session_state.observation
                    )
                    st.session_state.email_sent = True
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Erro ao processar documentos: {str(e)}")
        
        # Se o email foi enviado com sucesso, mostrar o resumo e o botão de reiniciar
        if st.session_state.email_sent:
            st.success("Documentos processados e enviados com sucesso!")
            
            # Mostrar resumo
            st.subheader("Resumo do envio:")
            st.write(f"Operação: {st.session_state.operation}")
            if st.session_state.observation:
                st.write(f"Nome da operação: {st.session_state.observation}")
            st.write(f"Quantidade de arquivos: {len(uploaded_files)}")
            st.write("Arquivos processados:")
            for file in uploaded_files:
                st.write(f"- {file.name}")
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("Iniciar Novo Processo", type="primary"):
                    st.session_state.email_sent = False
                    reset_all_states()
                    st.rerun()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Controle de Documentos",
        layout="wide",
        page_icon="📄"
    )
    main()