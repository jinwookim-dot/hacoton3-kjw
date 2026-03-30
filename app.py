# -*- coding: utf-8 -*-
"""
AI 멘토 웹 애플리케이션 - 다단계 UI + 대화 기능
"""
import streamlit as st
import os
from datetime import datetime
from ai_mentor import AIMentor
from data_processor import MentorKnowledgeBase
from ui_components import (
    get_custom_css, render_radar,
    render_icon_card, render_stat_card, render_hero_section
)

# 페이지 설정
st.set_page_config(
    page_title="AI 멘토 - 맥락에 맞는 일하는 방식",
    page_icon="💼",
    layout="wide"
)

# 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화"""
    if 'step' not in st.session_state:
        st.session_state.step = 1  # 1: 산업/직무, 2: 업무입력, 3: 조언+대화

    if 'mentor' not in st.session_state:
        st.session_state.mentor = None

    if 'kb' not in st.session_state:
        st.session_state.kb = None

    # 멘토 초기화 (config.py에서 자동으로 키 로드)
    if 'mentor_initialized' not in st.session_state:
        st.session_state.mentor_initialized = False

    # 단계별 입력 데이터

    if 'industry' not in st.session_state:
        st.session_state.industry = "선택 안함"
    if 'job_function' not in st.session_state:
        st.session_state.job_function = "선택 안함"

    if 'task_input' not in st.session_state:
        st.session_state.task_input = ""
    if 'supervisor_request' not in st.session_state:
        st.session_state.supervisor_request = ""
    if 'reference_files' not in st.session_state:
        st.session_state.reference_files = []

    # 대화 히스토리
    if 'initial_advice' not in st.session_state:
        st.session_state.initial_advice = ""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # 검색된 유사 사례
    if 'similar_cases' not in st.session_state:
        st.session_state.similar_cases = None

    # 세션 히스토리 관리
    if 'session_history' not in st.session_state:
        st.session_state.session_history = []
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

init_session_state()

# 커스텀 CSS 적용
st.markdown(get_custom_css(), unsafe_allow_html=True)

@st.cache_resource
def load_knowledge_base():
    """지식 베이스 로드 (캐싱)"""
    kb = MentorKnowledgeBase()
    if not kb.load_index():
        kb.build_index()
        kb.save_index()
    return kb

def init_mentor():
    """AI 멘토 초기화 (config.py에서 자동으로 키 로드)"""
    try:
        mentor = AIMentor()  # config.py에서 자동으로 키를 읽어옴
        return mentor, None
    except Exception as e:
        return None, str(e)

def go_to_step(step_num):
    """특정 단계로 이동"""
    st.session_state.step = step_num
    st.rerun()

def save_current_session():
    """현재 세션을 히스토리에 저장"""
    if st.session_state.initial_advice:  # 조언이 생성된 경우만 저장
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 세션 제목 생성 (업무 설명의 첫 30자 또는 산업/직무)
        title = st.session_state.task_input[:30] + "..." if len(st.session_state.task_input) > 30 else st.session_state.task_input
        if not title:
            title = f"{st.session_state.industry} - {st.session_state.job_function}"

        session_data = {
            'session_id': session_id,
            'title': title,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'industry': st.session_state.industry,
            'job_function': st.session_state.job_function,
            'task_input': st.session_state.task_input,
            'supervisor_request': st.session_state.supervisor_request,
            'reference_files': st.session_state.reference_files.copy() if st.session_state.reference_files else [],
            'initial_advice': st.session_state.initial_advice,
            'chat_history': st.session_state.chat_history.copy() if st.session_state.chat_history else [],
            'similar_cases': st.session_state.similar_cases.copy() if st.session_state.similar_cases is not None else None
        }

        # 기존 세션 업데이트 또는 새 세션 추가
        if st.session_state.current_session_id == session_id:
            # 기존 세션 업데이트
            for i, session in enumerate(st.session_state.session_history):
                if session['session_id'] == session_id:
                    st.session_state.session_history[i] = session_data
                    return

        # 새 세션 추가 (최신이 위로)
        st.session_state.session_history.insert(0, session_data)
        st.session_state.current_session_id = session_id

def load_session(session_id):
    """세션 로드"""
    for session in st.session_state.session_history:
        if session['session_id'] == session_id:
            st.session_state.industry = session['industry']
            st.session_state.job_function = session['job_function']
            st.session_state.task_input = session['task_input']
            st.session_state.supervisor_request = session['supervisor_request']
            st.session_state.reference_files = session['reference_files'].copy()
            st.session_state.initial_advice = session['initial_advice']
            st.session_state.chat_history = session['chat_history'].copy()
            st.session_state.similar_cases = session['similar_cases'].copy() if session['similar_cases'] is not None else None
            st.session_state.current_session_id = session_id
            st.session_state.step = 3  # 조언 페이지로 이동
            st.rerun()
            return

def start_new_session():
    """새 세션 시작"""
    # 현재 세션 저장
    if st.session_state.initial_advice:
        save_current_session()

    # 상태 초기화
    st.session_state.step = 1
    st.session_state.industry = "선택 안함"
    st.session_state.job_function = "선택 안함"
    st.session_state.task_input = ""
    st.session_state.supervisor_request = ""
    st.session_state.reference_files = []
    st.session_state.initial_advice = ""
    st.session_state.chat_history = []
    st.session_state.similar_cases = None
    st.session_state.current_session_id = None
    st.rerun()

def read_file_content(uploaded_file):
    """업로드된 파일 내용 읽기"""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode('utf-8')
        elif uploaded_file.type == "application/pdf":
            # PDF 읽기는 간단히 처리
            return f"[PDF 파일: {uploaded_file.name}]"
        else:
            return f"[파일: {uploaded_file.name}]"
    except:
        return f"[파일: {uploaded_file.name}]"

# KB 로드
if st.session_state.kb is None:
    st.session_state.kb = load_knowledge_base()
kb = st.session_state.kb

# 멘토 초기화 (처음 한 번만)
if not st.session_state.mentor_initialized:
    with st.spinner("🔧 AI 멘토 초기화 중... (config.py에서 AWS 키 로드)"):
        mentor, error = init_mentor()
        if error:
            st.error(f"❌ 초기화 실패: {error}")
            st.error("""
            **config.py 파일을 확인해주세요!**

            config.py 파일에 올바른 AWS 키를 입력했는지 확인하세요:
            - AWS_ACCESS_KEY_ID
            - AWS_SECRET_ACCESS_KEY
            - AWS_REGION
            """)
            st.stop()
        st.session_state.mentor = mentor
        st.session_state.mentor_initialized = True

# ====================
# 단계 1: 산업/직무 선택
# ====================
if st.session_state.step == 1:
    # 히어로 섹션
    st.markdown(render_hero_section(
        "💼 AI 멘토",
        "코멘토 직무부트캠프 944개 피드백 기반 맞춤형 멘토링"
    ), unsafe_allow_html=True)

    # 레이더 애니메이션
    st.markdown(render_radar(), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 메인 컨테이너
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>1단계: 산업 및 직무 선택</h2>", unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align: center; color: #64748b; margin-bottom: 2rem;'>
    여러분의 업무 맥락을 이해하기 위해 산업과 직무를 선택해주세요.<br>
    더 정확한 현직자 노하우를 제공할 수 있습니다.
    </p>
    """, unsafe_allow_html=True)

    # 통계 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(render_stat_card(f"{len(kb.df)}", "총 피드백"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_stat_card(f"{kb.df['industry'].nunique()}", "산업 분야"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_stat_card(f"{kb.df['mid_category'].nunique()}", "직무"), unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 선택 영역
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏢 산업 분야")
        industry = st.selectbox(
            "산업을 선택하세요",
            ["선택 안함"] + kb.get_industry_list(),
            index=(["선택 안함"] + kb.get_industry_list()).index(st.session_state.industry),
            help="여러분이 속한 산업 분야를 선택하세요",
            key="industry_select"
        )

    with col2:
        st.markdown("### 👔 직무")
        job_function = st.selectbox(
            "직무를 선택하세요",
            ["선택 안함"] + kb.get_job_list(),
            index=(["선택 안함"] + kb.get_job_list()).index(st.session_state.job_function),
            help="여러분의 직무를 선택하세요",
            key="job_select"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("다음 단계로 →", type="primary", use_container_width=True, key="step1_next"):
            st.session_state.industry = industry
            st.session_state.job_function = job_function
            go_to_step(2)

    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# 단계 2: 업무 입력
# ====================
elif st.session_state.step == 2:
    # 히어로 섹션
    st.markdown(render_hero_section(
        "📝 업무 정보 입력",
        "구체적인 정보를 제공할수록 더 정확한 조언을 받을 수 있습니다"
    ), unsafe_allow_html=True)

    # 메인 컨테이너
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>2단계: 업무 상세 정보</h2>", unsafe_allow_html=True)

    # 선택된 산업/직무 표시
    if st.session_state.industry != "선택 안함" or st.session_state.job_function != "선택 안함":
        selected_info = []
        if st.session_state.industry != "선택 안함":
            selected_info.append(f"🏢 {st.session_state.industry}")
        if st.session_state.job_function != "선택 안함":
            selected_info.append(f"👔 {st.session_state.job_function}")

        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                    border-radius: 12px; padding: 1rem; margin-bottom: 2rem; text-align: center;'>
            <strong>선택된 정보:</strong> {' | '.join(selected_info)}
        </div>
        """, unsafe_allow_html=True)

    # 1. 업무 설명
    st.markdown("### 📋 수행할 업무")
    st.markdown("<p style='color: #64748b; font-size: 0.875rem; margin-bottom: 1rem;'>어떤 업무를 수행해야 하는지 구체적으로 작성해주세요</p>", unsafe_allow_html=True)
    task_input = st.text_area(
        "업무를 구체적으로 설명해주세요",
        value=st.session_state.task_input,
        height=150,
        placeholder="""예시:
- 신제품 출시를 위한 SNS 마케팅 캠페인 기획
- 제품 불량률 개선을 위한 품질 분석 보고서 작성
- 고객 이탈 방지를 위한 CRM 전략 수립""",
        help="어떤 업무를 수행해야 하는지 구체적으로 작성해주세요"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 사수 요청사항
    st.markdown("### 👨‍💼 사수의 요청사항 (선택)")
    st.markdown("<p style='color: #64748b; font-size: 0.875rem; margin-bottom: 1rem;'>사수가 말한 내용을 최대한 원문 그대로 입력하면 더 정확한 조언을 받을 수 있습니다</p>", unsafe_allow_html=True)
    supervisor_request = st.text_area(
        "사수가 요청한 내용을 원문 그대로 입력해주세요",
        value=st.session_state.supervisor_request,
        height=120,
        placeholder="""예시:
"이번 캠페인은 2535 타겟으로 하되, 인스타그램과 틱톡 중심으로 기획해줘.
예산은 500만원이고, 다음 주 월요일까지 초안 부탁해."
""",
        help="사수가 말한 내용을 최대한 원문 그대로 입력하면 더 정확한 조언을 받을 수 있습니다"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. 참고 데이터
    st.markdown("### 📎 참고 데이터 / 이전 작업물 (선택)")
    st.markdown("<p style='color: #64748b; font-size: 0.875rem; margin-bottom: 1rem;'>관련 문서나 이전에 작성한 유사 작업물이 있다면 첨부해주세요</p>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "파일 업로드",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'docx', 'xlsx', 'pptx'],
        help="텍스트 파일, PDF, Word, Excel, PowerPoint 파일을 업로드할 수 있습니다"
    )

    reference_text = st.text_area(
        "또는 참고 내용을 직접 입력",
        height=100,
        placeholder="이전 작업물의 내용이나 참고할 만한 정보를 입력하세요"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 뒤로", use_container_width=True, key="step2_back"):
            st.session_state.task_input = task_input
            st.session_state.supervisor_request = supervisor_request
            go_to_step(1)
    with col3:
        if st.button("AI 조언 받기 🚀", type="primary", use_container_width=True, key="step2_next"):
            if not task_input.strip():
                st.error("⚠️ 업무 설명을 입력해주세요!")
            else:
                # 데이터 저장
                st.session_state.task_input = task_input
                st.session_state.supervisor_request = supervisor_request

                # 파일 처리
                reference_data = []
                if uploaded_files:
                    for file in uploaded_files:
                        content = read_file_content(file)
                        reference_data.append(f"[파일: {file.name}]\n{content}")

                if reference_text.strip():
                    reference_data.append(reference_text)

                st.session_state.reference_files = reference_data

                # 유사 사례 검색
                search_query = task_input
                if st.session_state.industry != "선택 안함":
                    search_query = f"{st.session_state.industry} {search_query}"
                if st.session_state.job_function != "선택 안함":
                    search_query = f"{st.session_state.job_function} {search_query}"

                st.session_state.similar_cases = kb.search(search_query, top_k=5)

                # 초기 조언 생성
                with st.spinner("🤔 AI 멘토가 조언을 생성하고 있습니다... (30초~1분 소요)"):
                    try:
                        advice = st.session_state.mentor.generate_advice(
                            task_description=task_input,
                            industry=st.session_state.industry if st.session_state.industry != "선택 안함" else None,
                            job_function=st.session_state.job_function if st.session_state.job_function != "선택 안함" else None,
                            supervisor_request=supervisor_request if supervisor_request.strip() else None,
                            reference_data="\n\n".join(reference_data) if reference_data else None,
                            top_k=5
                        )
                        st.session_state.initial_advice = advice
                        st.session_state.chat_history = []  # 대화 초기화
                        save_current_session()  # 세션 저장
                        go_to_step(3)
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# ====================
# 단계 3: AI 조언 + 대화
# ====================
elif st.session_state.step == 3:
    # 히어로 섹션
    st.markdown(render_hero_section(
        "🎓 AI 멘토의 조언",
        "현직자 데이터 기반 맞춤형 조언을 확인하고 추가 질문을 해보세요"
    ), unsafe_allow_html=True)

    # 사이드바 - 세션 히스토리 및 입력 정보 요약
    with st.sidebar:
        # 새 세션 시작 버튼
        if st.button("✨ 새 세션 시작", use_container_width=True, type="primary"):
            # 현재 세션 저장
            save_current_session()
            start_new_session()

        st.markdown("---")

        # 세션 히스토리
        if st.session_state.session_history:
            st.markdown("### 📚 대화 기록")
            for session in st.session_state.session_history[:5]:  # 최근 5개만 표시
                is_current = session['session_id'] == st.session_state.current_session_id
                label = "🟢 " + session['title'] if is_current else session['title']
                if st.button(
                    label,
                    use_container_width=True,
                    key=f"session_{session['session_id']}",
                    help=f"{session['created_at']}"
                ):
                    if not is_current:
                        # 현재 세션 저장
                        save_current_session()
                        # 선택한 세션 로드
                        load_session(session['session_id'])

            st.markdown("---")

        st.markdown("### 📝 입력 정보")
        if st.session_state.industry != "선택 안함":
            st.write(f"**산업:** {st.session_state.industry}")
        if st.session_state.job_function != "선택 안함":
            st.write(f"**직무:** {st.session_state.job_function}")

        st.markdown("---")

        with st.expander("📋 업무 내용"):
            st.write(st.session_state.task_input)

        if st.session_state.supervisor_request:
            with st.expander("👨‍💼 사수 요청사항"):
                st.write(st.session_state.supervisor_request)

        if st.session_state.reference_files:
            with st.expander("📎 참고 데이터"):
                st.write(f"{len(st.session_state.reference_files)}개의 참고 자료")

        st.markdown("---")

        if st.button("← 업무 수정", use_container_width=True):
            go_to_step(2)

        if st.button("← 산업/직무 변경", use_container_width=True):
            go_to_step(1)

    # 메인 컨테이너
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # 초기 조언
    st.markdown("### 🎓 AI 멘토의 초기 조언")
    st.markdown('<div style="background: rgba(45, 45, 45, 0.8); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border: 1px solid rgba(255, 255, 255, 0.1);">', unsafe_allow_html=True)
    st.markdown(st.session_state.initial_advice)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 대화 섹션
    st.markdown("### 💬 추가 질문하기")
    st.markdown("<p style='color: rgba(255, 255, 255, 0.8); margin-bottom: 1rem;'>조언에 대해 궁금한 점이 있거나, 더 구체적인 내용이 필요하면 질문해주세요.</p>", unsafe_allow_html=True)

    # 대화 히스토리 표시
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="chat-message user">{chat["user"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-message assistant">{chat["assistant"]}</div>', unsafe_allow_html=True)

    # 파일 첨부 기능
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_chat_files = st.file_uploader(
        "📎 추가 자료 첨부 (선택사항)",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'docx', 'xlsx', 'pptx'],
        help="질문과 함께 참고할 파일을 첨부할 수 있습니다",
        key="chat_file_uploader"
    )

    # 새 질문 입력
    user_question = st.chat_input("질문을 입력하세요...")

    if user_question:
        with st.spinner("🤔 답변 생성 중..."):
            try:
                # 첨부된 파일 처리
                attached_files_text = ""
                if uploaded_chat_files:
                    attached_files_text = "\n\n[첨부된 파일]\n"
                    for file in uploaded_chat_files:
                        content = read_file_content(file)
                        attached_files_text += f"{content}\n\n"

                # 질문에 파일 내용 추가
                full_question = user_question
                if attached_files_text:
                    full_question = f"{user_question}\n{attached_files_text}"

                # 대화 컨텍스트 구성
                context = f"""
[이전 조언]
{st.session_state.initial_advice}

[대화 히스토리]
"""
                for chat in st.session_state.chat_history:
                    context += f"\n사용자: {chat['user']}\nAI 멘토: {chat['assistant']}\n"

                # 추가 질문에 대한 답변 생성
                answer = st.session_state.mentor.continue_conversation(
                    user_question=full_question,
                    conversation_context=context,
                    task_description=st.session_state.task_input,
                    industry=st.session_state.industry if st.session_state.industry != "선택 안함" else None,
                    job_function=st.session_state.job_function if st.session_state.job_function != "선택 안함" else None
                )

                # 대화 히스토리 저장 (파일 첨부 표시 포함)
                user_display_message = user_question
                if uploaded_chat_files:
                    file_names = ", ".join([f.name for f in uploaded_chat_files])
                    user_display_message += f"<br><small style='color: #88a0ff;'>📎 첨부: {file_names}</small>"

                st.session_state.chat_history.append({
                    'user': user_display_message,
                    'assistant': answer
                })

                # 세션 업데이트
                save_current_session()

                st.rerun()
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

    # 참고한 유사 사례
    if st.session_state.similar_cases is not None:
        st.markdown("---")
        with st.expander("📚 참고한 유사 사례들", expanded=False):
            for idx, row in st.session_state.similar_cases.iterrows():
                st.markdown(f"""
                <div style='background: rgba(45, 45, 45, 0.8); border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; border: 1px solid rgba(255, 255, 255, 0.1);'>
                    <strong style='color: white;'>[사례 {idx + 1}] {row['industry']} - {row['mid_category']}</strong><br>
                    <span style='color: rgba(255, 255, 255, 0.8);'>과제: {row['title']}</span><br>
                    <span style='color: #88a0ff;'>유사도: {row['similarity']:.1%}</span>
                </div>
                """, unsafe_allow_html=True)

    # 돌아가기 버튼
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 업무 다시 입력하기", use_container_width=True, key="main_back_to_step2"):
            go_to_step(2)
    with col2:
        if st.button("← 처음으로", use_container_width=True, key="main_back_to_step1"):
            go_to_step(1)

    st.markdown('</div>', unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: rgba(255, 255, 255, 0.6);'>
    <p>코멘토 직무부트캠프 데이터 기반 | 944개 실제 멘토 피드백 학습</p>
    <p>AWS Bedrock Claude 3.5 Sonnet | Made with ❤️ for 해커톤</p>
</div>
""", unsafe_allow_html=True)
