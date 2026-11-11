"""F1 Quiz: ten questions written from the archive, one at a time, with a score and a
share card at the end."""
import streamlit as st

import archive
from app_archive import require_history
from cards import cards_css, note
from quiz import ERAS, build
from quiz_card import quiz_card
from style import empty_note, stat_strip

QUESTIONS = 10
STATE = "quiz"

cards_css()
require_history()


def verdict(score, total):
    share = score / total if total else 0
    if share == 1:
        return "Perfect. Every single one."
    if share >= 0.8:
        return "Serious form."
    if share >= 0.6:
        return "A solid points finish."
    if share >= 0.4:
        return "Midfield. Room to improve."
    if share > 0:
        return "A difficult weekend."
    return "Lights out and away we go... next time."


def start(era):
    """Begin a new quiz. Each one gets its own id, which goes into the answer widget's
    key: without it a second quiz would inherit the first one's selected answers, and
    Streamlit would choke when an old answer is not among the new options."""
    questions = build(QUESTIONS, era=era)
    st.session_state["quiz_round"] = st.session_state.get("quiz_round", 0) + 1
    st.session_state[STATE] = {
        "questions": questions, "era": era, "at": 0,
        "id": st.session_state["quiz_round"],
        "answers": [], "marks": [], "checked": False,
    }


# ---------- no quiz running: the start screen ----------

if STATE not in st.session_state:
    st.subheader("Ten questions, straight from the record books")
    note("Nothing here is hand-written trivia. Every question is built from the real "
         "results, every wrong answer is a real driver, team or number from the same "
         "race or season, and after each one you are told exactly where the answer comes "
         "from. No two quizzes are the same.")
    era = st.selectbox("Which era?", list(ERAS))
    if st.button("Start the quiz", type="primary"):
        start(era)
        st.rerun()
    st.stop()

state = st.session_state[STATE]
questions = state["questions"]

if not questions:
    empty_note("No questions could be made from the archive.")
    del st.session_state[STATE]
    st.stop()

# ---------- the quiz is finished ----------

if state["at"] >= len(questions):
    score = sum(state["marks"])
    stat_strip([
        ("Your score", f'{score}/{len(questions)}', verdict(score, len(questions)), True),
        ("Era", state["era"], "the questions were drawn from here", False),
        ("Right first time", f'{100 * score / len(questions):.0f}%', "of the ten", False),
    ])

    quiz_card(score, len(questions), state["era"], state["marks"],
              verdict(score, len(questions)))

    st.subheader("Every question, and the answer")
    for i, (question, given, hit) in enumerate(
            zip(questions, state["answers"], state["marks"]), start=1):
        mark = "✅" if hit else "❌"
        with st.expander(f'{mark}  {i}. {question["question"]}', expanded=not hit):
            if not hit:
                st.markdown(f'You said **{given}**.')
            st.markdown(f'The answer is **{question["answer"]}**. {question["explain"]}')

    left, right = st.columns(2)
    with left:
        if st.button("Play again, same era", type="primary"):
            start(state["era"])
            st.rerun()
    with right:
        if st.button("Pick a different era"):
            del st.session_state[STATE]
            st.rerun()
    st.stop()

# ---------- one question at a time ----------

at = state["at"]
question = questions[at]
done = sum(state["marks"])

pills = "".join(
    f'<div class="pp-step{" on" if i == at else ""}">{"✓" if i < at and state["marks"][i] else ("✗" if i < at else i + 1)}</div>'
    for i in range(len(questions)))
st.markdown(f'<div class="pp-steps">{pills}</div>', unsafe_allow_html=True)
st.caption(f'Question {at + 1} of {len(questions)} · {question["kind"]} · '
           f'{done} right so far')

st.subheader(question["question"])
choice = st.radio("Your answer", question["options"], index=None,
                  key=f'choice_{state.get("id", 0)}_{at}',
                  label_visibility="collapsed")

if not state["checked"]:
    if st.button("Check my answer", type="primary", disabled=choice is None):
        state["answers"].append(choice)
        state["marks"].append(choice == question["answer"])
        state["checked"] = True
        st.rerun()
    if choice is None:
        note("Pick one of the four to carry on.")
else:
    if state["marks"][-1]:
        st.success(f'Right. {question["explain"]}')
    else:
        st.error(f'Not this time. The answer is **{question["answer"]}**. '
                 f'{question["explain"]}')
    label = "Next question" if at + 1 < len(questions) else "See my score"
    if st.button(label, type="primary"):
        state["at"] += 1
        state["checked"] = False
        st.rerun()
