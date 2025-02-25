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


def criar_pdf(operation, observation, uploaded_files, doc_checks, responsible_name):
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

    # Adicionar seção de verificações
    story.append(Paragraph("Verificações realizadas:", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Lista de verificações
    verificacoes = [
        ("O documento está assinado?", doc_checks['doc_signed']),
        ("O documento está datado?", doc_checks['doc_dated']),
        ("Todos os comprovantes relacionados à carga estão em anexo?", doc_checks['all_attachments'])
    ]
    
    for descricao, status in verificacoes:
        status_text = "✓ Sim" if status else "✗ Não"
        story.append(Paragraph(f"• {descricao} {status_text}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("✓ Usuário confirmou ciência da responsabilidade pela conferência dos itens.", styles['Normal']))
    
    # Adicionar nome do responsável
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Responsável pela verificação: {responsible_name}", styles['Normal']))
    story.append(Spacer(1, 30))

    # Adicionar documentos
    story.append(Paragraph("Documentos anexados:", styles['Heading2']))
    story.append(Spacer(1, 10))
    
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

def load_css():
    with open('style.css', 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    # Carregar o CSS customizado
    try:
        load_css()
    except FileNotFoundError:
        st.write("Arquivo de estilo não encontrado. A aplicação funcionará com o estilo padrão.")
    
    # Adicionando ícone e título com estilo
    st.markdown('<h1><span style="display: flex; align-items: center;"><svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" viewBox="0 0 16 16" style="margin-right: 10px;"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zM4.5 9a.5.5 0 0 1 0-1h7a.5.5 0 0 1 0 1h-7zM4 10.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm.5 2.5a.5.5 0 0 1 0-1h4a.5.5 0 0 1 0 1h-4z"/></svg>Controle de Documentos</span></h1>', unsafe_allow_html=True)
    
    # Inicialização das variáveis de sessão
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'operation' not in st.session_state:
        st.session_state.operation = ""
    if 'observation' not in st.session_state:
        st.session_state.observation = ""
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = False
        
    # Indicador de progresso
    progress_percent = (st.session_state.step - 1) / 3
    st.progress(progress_percent)
    steps_text = ["Selecionar Operação", "Verificação do Documento", "Anexar e Enviar"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div style="text-align: center; {"font-weight:bold;" if st.session_state.step == 1 else ""} {"color: var(--primary-color);" if st.session_state.step >= 1 else ""}">1. {steps_text[0]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="text-align: center; {"font-weight:bold;" if st.session_state.step == 2 else ""} {"color: var(--primary-color);" if st.session_state.step >= 2 else ""}">2. {steps_text[1]}</div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div style="text-align: center; {"font-weight:bold;" if st.session_state.step == 3 else ""} {"color: var(--primary-color);" if st.session_state.step >= 3 else ""}">3. {steps_text[2]}</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
        
    # Passo 1: Seleção da operação
    if st.session_state.step == 1:
        st.header("1º Passo: Selecionar Operação")
        
        with st.container():
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
                    
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Próximo", use_container_width=True):
                    st.session_state.operation = operation
                    st.session_state.observation = observation
                    st.session_state.step = 2
                    st.rerun()
            
    # Passo 2: Verificação do documento

    elif st.session_state.step == 2:
        st.header("2º Passo: Verificação do Documento")
        
        st.markdown(f"<div style='margin-bottom: 20px; padding: 10px; border-radius: 5px; background-color: var(--background-color-transparent);'><strong>Operação:</strong> {st.session_state.operation} {st.session_state.observation}</div>", unsafe_allow_html=True)
        
        with st.container():
            # Inicializar os valores na session_state se não existirem
            if 'doc_signed' not in st.session_state:
                st.session_state.doc_signed = False
            if 'doc_dated' not in st.session_state:
                st.session_state.doc_dated = False
            if 'all_attachments' not in st.session_state:
                st.session_state.all_attachments = False
            if 'responsible_name' not in st.session_state:
                st.session_state.responsible_name = ""
            
            st.subheader("Verificações do documento")
            # Checkboxes não obrigatórias
            st.session_state.doc_signed = st.checkbox(
                "O documento está assinado?",
                value=st.session_state.doc_signed,
                key='doc_signed_checkbox'
            )
            st.session_state.doc_dated = st.checkbox(
                "O documento está datado?",
                value=st.session_state.doc_dated,
                key='doc_dated_checkbox'
            )
            st.session_state.all_attachments = st.checkbox(
                "Todos os comprovantes relacionados à carga estão em anexo?",
                value=st.session_state.all_attachments,
                key='all_attachments_checkbox'
            )
            
            # Adiciona espaço entre os grupos de checkboxes
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Nova checkbox obrigatória de responsabilidade
            st.subheader("Termo de responsabilidade")
            responsibility_check = st.checkbox(
                "✓ Estou ciente que é de minha responsabilidade conferir os itens acima.",
                key='responsibility_check'
            )
            
            # Campo para nome do responsável
            st.session_state.responsible_name = st.text_input(
                "Nome do responsável:",
                value=st.session_state.responsible_name,
                key='responsible_name_input'
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Voltar", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()
            with col3:
                if st.button("Próximo", use_container_width=True):
                    if not responsibility_check:
                        st.error("Você precisa confirmar que está ciente da sua responsabilidade para prosseguir.")
                        return
                    
                    if not st.session_state.responsible_name.strip():
                        st.error("Por favor, preencha o nome do responsável.")
                        return
                        
                    st.session_state.step = 3
                    st.rerun()
            
    # Passo 3: Upload e envio

    elif st.session_state.step == 3:
        st.header("3º Passo: Anexar e Enviar Documentos")
        
        st.markdown(f"<div style='margin-bottom: 20px; padding: 10px; border-radius: 5px; background-color: var(--background-color-transparent);'><strong>Operação:</strong> {st.session_state.operation} {st.session_state.observation}</div>", unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Selecione o(s) documento(s):",
            accept_multiple_files=True,
            type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
            key='file_uploader'
        )
        
        # Mostrar arquivos selecionados
        if uploaded_files:
            st.subheader("Documentos selecionados:")
            for file in uploaded_files:
                # Determinar ícone com base no tipo de arquivo
                file_icon = "📄"  # Ícone padrão
                if file.type.startswith('image/'):
                    file_icon = "🖼️"
                elif file.type == 'application/pdf':
                    file_icon = "📑"
                elif 'word' in file.type:
                    file_icon = "📝"
                
                # Mostrar arquivo com ícone e tamanho
                file_size = len(file.getvalue()) / 1024  # Tamanho em KB
                size_text = f"{file_size:.1f} KB" if file_size < 1024 else f"{file_size/1024:.1f} MB"
                
                st.markdown(f"""
                <div class="file-card">
                    <div class="file-icon">{file_icon}</div>
                    <div>{file.name} <span style="color: gray; font-size: 0.8em;">({size_text})</span></div>
                </div>
                """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Voltar", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with col3:
            if st.button("Enviar", use_container_width=True):
                if not uploaded_files:
                    st.error("Por favor, anexe pelo menos um documento.")
                    return
                
                try:
                    with st.spinner("Processando documentos e enviando email..."):
                        # Criar dicionário com o status das verificações
                        doc_checks = {
                            'doc_signed': st.session_state.doc_signed,
                            'doc_dated': st.session_state.doc_dated,
                            'all_attachments': st.session_state.all_attachments
                        }
                        
                        # Criar PDF
                        pdf_buffer = criar_pdf(
                            st.session_state.operation,
                            st.session_state.observation,
                            uploaded_files,
                            doc_checks,
                            st.session_state.responsible_name
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
            st.markdown("""
            <div class="success-message">
                <h3 style="margin-top: 0;">✅ Documentos processados e enviados com sucesso!</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar resumo
            st.subheader("Resumo do envio:")
            
            st.markdown(f"""
            <div class="detail-container">
                <p><strong>Operação:</strong> {st.session_state.operation}</p>
                {"<p><strong>Nome da operação:</strong> " + st.session_state.observation + "</p>" if st.session_state.observation else ""}
                <p><strong>Responsável:</strong> {st.session_state.responsible_name}</p>
                <p><strong>Quantidade de arquivos:</strong> {len(uploaded_files)}</p>
                <p><strong>Data/Hora:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("Iniciar Novo Processo", type="primary", use_container_width=True):
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