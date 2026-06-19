import streamlit as st

from app.models import MODEL_CHOICES, MODEL_GPT, MODEL_OPTIONS, chat_with_model, get_model_fn
from app.prompts import CHAT_SYSTEM_PROMPT
from app.story_engine import format_evaluation, judge_and_refine_story
from app.story_output import parse_story, story_only
from main import call_model


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = MODEL_GPT


def clear_conversation() -> None:
    st.session_state.messages = []


def build_model_messages() -> list[dict[str, str]]:
    chat_messages = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    return [{"role": "system", "content": CHAT_SYSTEM_PROMPT}, *chat_messages]


def render_header() -> str:
    st.title("Bedtime Story Chat")
    st.caption("Create and refine bedtime stories for ages 5-10.")

    col_model, col_clear = st.columns([3, 1])
    with col_model:
        model = st.selectbox(
            "Model",
            options=MODEL_CHOICES,
            format_func=lambda name: MODEL_OPTIONS[name]["label"],
            key="model_selector",
        )
    with col_clear:
        st.write("")
        if st.button("Clear conversation"):
            clear_conversation()
            st.rerun()

    if model != st.session_state.selected_model:
        st.session_state.selected_model = model
        clear_conversation()
        st.info(f"Switched to {MODEL_OPTIONS[model]['label']}. Conversation history was reset.")

    if model == MODEL_GPT and not _env_openai_key():
        st.warning("Set `OPENAI_API_KEY` to use gpt-3.5-turbo.")

    return model


def _env_openai_key() -> bool:
    import os

    return bool(os.getenv("OPENAI_API_KEY"))


def render_story(content: str) -> None:
    title, body = parse_story(content)
    if title:
        st.title(title)
    if body:
        st.markdown(body)


def render_evaluation_scores(evaluation: dict) -> None:
    with st.expander("Story evaluation"):
        st.markdown(format_evaluation(evaluation))


def render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_story(message["content"])
                if evaluation := message.get("evaluation"):
                    render_evaluation_scores(evaluation)
            else:
                st.markdown(message["content"])


def handle_user_prompt(model: str, prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Writing story..."):
                draft = story_only(chat_with_model(model, build_model_messages()))

            model_fn = get_model_fn(model, call_model)
            with st.spinner("Evaluating story..."):
                response, evaluation = judge_and_refine_story(draft, model_fn)
            response = story_only(response)
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")
            st.session_state.messages.pop()
            return

        render_story(response)
        render_evaluation_scores(evaluation)

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "evaluation": evaluation}
    )


def main() -> None:
    st.set_page_config(page_title="Bedtime Story Chat", page_icon="🌙", layout="centered")
    init_session_state()
    model = render_header()
    render_chat_history()

    if prompt := st.chat_input("Ask for a story or request changes..."):
        handle_user_prompt(model, prompt)


if __name__ == "__main__":
    main()
