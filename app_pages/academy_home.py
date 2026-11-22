"""Engineering Academy: the course map, your progress and the glossary."""
import html

import streamlit as st

from academy import CURRICULUM, GLOSSARY, academy_css, progress
from style import stat_strip
from ui_kit import section

academy_css()

# Modules that have pages so far. Add a line here when a module goes live.
LIVE = {"0": "app_pages/academy_m0.py", "1": "app_pages/academy_m1.py", "2": "app_pages/academy_m2.py",
        "3": "app_pages/academy_m3.py",
        "4": "app_pages/academy_m4.py",
        "5": "app_pages/academy_m5.py", "6": "app_pages/academy_m6.py", "7": "app_pages/academy_m7.py",
        "11": "app_pages/academy_m11.py", "12": "app_pages/academy_m12.py"}

st.markdown("""
How a modern Formula 1 car works and how a race is engineered, from the tyres up. Every chapter
comes in three depths (**Basics**, **Engineer** and **Deep dive**), runs live demos on the same
physics engines as the Simulator pages, and links to the real race data in the rest of the app.
""")
left, right = st.columns(2)
left.page_link(LIVE["0"], label="Start the course: Module 0", icon=":material/school:", use_container_width=True)
right.page_link("app_pages/academy_parts.py", label="Take the car apart in 3D",
                icon=":material/view_in_ar:", use_container_width=True)

total = sum(len(chapters) for _, _, chapters in CURRICULUM)
live_chapters = sum(len(chapters) for n, _, chapters in CURRICULUM if n in LIVE)
done = progress()["read"]
scores = progress()["quiz"].values()
stat_strip([
    ("Modules", f"{len(CURRICULUM)}", f"{len(LIVE)} open now, more after each update", True),
    ("Chapters", f"{total}", f"{live_chapters} open now", False),
    ("Read this visit", f"{len(done)}", "chapters opened", False),
    ("Quiz answers right", f"{sum(s for s, _ in scores)}/{sum(t for _, t in scores)}" if scores else "–",
     "this visit", False),
])

section("The course", "Open modules have a link. The rest are on their way, in this order.")
cols = st.columns(3)
for i, (number, title, chapters) in enumerate(CURRICULUM):
    live = number in LIVE
    tag = ('<span class="tag" style="color:#1fd6a0">Open</span>' if live
           else '<span class="tag" style="color:var(--pp-muted)">Coming soon</span>')
    items = "".join(f"<li>{html.escape(c)}</li>" for c in chapters)
    with cols[i % 3]:
        st.markdown(f'<div class="ac-mod">{tag}<h4>{number}. {html.escape(title)}</h4><ol>{items}</ol></div>',
                    unsafe_allow_html=True)
        if live:
            st.page_link(LIVE[number], label=f"Open Module {number}", icon=":material/arrow_forward:")
        st.write("")

section("Glossary", "Every term the course uses, in plain words.")
query = st.text_input("Search the glossary", placeholder="e.g. downforce", label_visibility="collapsed")
terms = sorted(GLOSSARY.items(), key=lambda kv: kv[0].lower())
if query:
    q = query.lower()
    terms = [(t, d) for t, d in terms if q in t.lower() or q in d.lower()]
if terms:
    st.markdown("".join(f'<div class="ac-term"><b>{html.escape(t)}</b><span>{html.escape(d)}</span></div>'
                        for t, d in terms), unsafe_allow_html=True)
else:
    st.caption("Nothing matches that yet.")
