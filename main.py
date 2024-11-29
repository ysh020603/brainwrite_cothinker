from  brainwrite_cothinker import *
import streamlit as st
from typing import Literal
import os


def show_and_record(show_content:str, role:str=Literal["assistant", "user"])-> None:
    st.chat_message(role).write(show_content)
    st.session_state.messages.append({"role": role, "content": show_content})

def show_and_record_cothinker(show_content:str, role:str=Literal["cothinker", "user"]) -> None:
    st.session_state.cothinker.append({"role": role, "content": show_content})
    if role == "cothinker":
        st.chat_message(role, avatar="✌").write(show_content)
    else:
        st.chat_message(role).write(show_content)



st.title("Brainwrite with LLM experts 🧠")

# 侧边栏中的选项
with st.sidebar:
    api_key = st.text_input("API Key", key="chatbot_api_key", type="password")
    model = st.selectbox("Model", ["glm-4-flash", "glm-4-air", "glm-4-plus"])
    expert_number = st.number_input("Insert a number",max_value=5, min_value=3, value=4)
    topic = st.text_area("Input the brainstorm topic")
    intent = st.text_area("Input the brainstorm intent (optional)")

            
    
if "brainstorm" not in st.session_state:
    st.session_state["if_begin"] = False
    begin_prompt = """
**Brainwrite** is a creative technique used to generate ideas within a group setting. 

**Process:**
1. **Define the Problem:** Start by clearly stating the problem or topic that needs to be addressed.
2. **Individual Writing:** Each participant writes down their ideas individually, often on a sheet of paper or a digital platform.
3. **Passing Ideas:** After a set time, participants pass their ideas to the next person, who then adds to or builds upon them.
4. **Rounds of Writing:** This process is repeated for several rounds to ensure that all ideas are shared and developed.
5. **Review and Discussion:** Once all ideas have been collected, the group reviews them and discusses the most promising ones.

You can get api key in 
- [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
"""
    st.session_state["messages"] = [{"role": "assistant", "content": begin_prompt}]
    st.session_state["cothinker"] = []


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if st.sidebar.button("restart 🎈"):
    if "brainstorm" in st.session_state:
        del st.session_state["brainstorm"]
        st.session_state["if_begin"] = False
        st.rerun()
    else:
        st.rerun()
        
if st.session_state["if_begin"] == False:
    if st.sidebar.button("begin 🎯"):
        if not api_key:
            st.info("Please add your API key to continue.")
            st.stop()
        if not topic:
            st.info("Please input the brainstorm topic.")
            st.stop()
        st.session_state["if_begin"] = True
        current_file_path = os.path.abspath(__file__)
        current_file_directory = os.path.dirname(current_file_path)
        background_path = current_file_directory + r"\data\background_short.json"
        url = "https://open.bigmodel.cn/api/paas/v4/"
        st.session_state["brainstorm"] = Brainwrite(api_key=api_key, 
                                                    url=url, 
                                                    model=model, 
                                                    background_path=background_path,
                                                    topic=topic)
        with st.spinner("Loading..."):
            expert_list = st.session_state["brainstorm"].choose_expert(expert_n=expert_number-1)
            show_topic_expert = f"Based on the topic **{topic}** you gave, the LLM has selected the following experts:\n\n"
            for name in expert_list:
                show_topic_expert += f"- {name}\n\n"
            show_and_record(show_topic_expert, role="assistant")

        with st.spinner("Loading..."):
            topic_aug = st.session_state["brainstorm"].augment_background(intent)
            show_topic_aug = f"According to the topic **{topic}** you gave, LLM has been expanded as follows:\n\n{topic_aug}"
            show_and_record(show_topic_aug, role="assistant")

        with st.spinner("🧠 You can start thinking and type later."):
            st.session_state["brainstorm"].brainwrite()
            prompt_begin = f"Please start writing the note. 📄"
            show_and_record(prompt_begin, role="assistant")
        st.rerun()
            

if prompt := st.chat_input(key="main"):
    if not api_key:
        st.info("Please add your API key to continue.")
        st.stop()
    elif not topic:
        st.info("Please input the brainstorm topic.")
        st.stop()
    elif "brainstorm" not in st.session_state:
        st.info("Please initiate the brainstorm first")
        st.stop()
    else:
        if  st.session_state["brainstorm"].record["now"]<len(st.session_state["brainstorm"].record["expert_name"]):
            show_and_record(prompt, role="user")
            st.session_state["brainstorm"].human_input_brainwrite(prompt)
            show_and_record(st.session_state["brainstorm"].paper_content_before_input(), role="assistant")
            

            with st.spinner("🧠 You can start thinking and type later."):
                st.session_state["brainstorm"].brainwrite()
                prompt_begin = f"Please start writing the note. 📄"
                show_and_record(prompt_begin, role="assistant")

        elif st.session_state["brainstorm"].record["now"]==len(st.session_state["brainstorm"].record["expert_name"]):
            show_and_record(prompt, role="user")
            st.session_state["brainstorm"].human_input_brainwrite(prompt)
            show_and_record("over", role="assistant")

        if st.session_state["brainstorm"].record["now"] >1 and st.session_state["brainstorm"].record["now"]<=len(st.session_state["brainstorm"].record["expert_name"]):
            st.session_state["cothinker"] = [{"role":"cothinker","content":st.session_state["brainstorm"].cothinker_summary()}]
            st.rerun()
        

if "cothinker" in st.session_state and "brainstorm" in st.session_state: 
    if st.session_state["brainstorm"].record["now"]<=len(st.session_state["brainstorm"].record["expert_name"]):
        with st.popover("cothinker ✌"):
            st.markdown("cothinker 👋")
            if st.session_state["cothinker"] != []:
                for msg in st.session_state.cothinker:
                    if msg["role"] == "cothinker":
                        st.chat_message(msg["role"],avatar="✌").write(msg["content"])
                    else:
                        st.chat_message(msg["role"]).write(msg["content"])
            if prompt := st.chat_input(key="cothinker_interaction"):
                if "brainstorm" not in st.session_state:
                    st.info("Please initiate the game first")
                    
                elif not api_key:
                    st.info("Please add your API key to continue.")
                    
                elif not topic:
                    st.info("Please input the brainstorm topic.")
                    
                elif st.session_state["brainstorm"].record["now"]>len(st.session_state["brainstorm"].record["expert_name"]):
                    st.info("The brainstorm is over.")
                else:
                    show_and_record_cothinker(prompt, "user")
                    get_interaction = st.session_state["brainstorm"].cothinker_interaction(prompt)
                    show_and_record_cothinker(get_interaction, "cothinker")
                    st.rerun()

if "brainstorm" in st.session_state:
    if st.session_state["brainstorm"].record["now"]>len(st.session_state["brainstorm"].record["expert_name"]):
        for name in st.session_state["brainstorm"].record["expert_name"]:
            show_paper = f"This is **{name}'s** note.📃\n\n{st.session_state["brainstorm"].record["paper_%s"%name]}"
            show_and_record(show_paper, role="assistant")

if "brainstorm" in st.session_state:
    if st.session_state["brainstorm"].record["now"]>len(st.session_state["brainstorm"].record["expert_name"]):
        st.info("The brainstorm is over.")



