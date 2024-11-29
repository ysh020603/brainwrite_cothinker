import threading
from package import openai_sdk as sdk
import re
import json
from typing import List, Dict, Any
import copy




class Brainwrite:

    
    def __init__(self, 
                 api_key:str, 
                 url:str = "https://open.bigmodel.cn/api/paas/v4/", 
                 model:str = "glm-4-flash", 
                 background_path:str=r"data/background_short.json", 
                 topic:str=" ")->None:
        '''
        - api_key: api key

        - url: url

        - model: model

        - background_path: background_path
        '''
        self.api_key = api_key
        self.url = url
        self.model = model
        self.background_path = background_path
        self.record = {}
        self.record["topic"] = topic
        self.lock = threading.Lock()

    def contains_chinese_text(self,text):
        '''
        divide text into chinese and english
        chinese True
        '''
        return bool(re.search('[\u4e00-\u9fff]', text))
    
    def call_api(self, prompt:List[dict])->str:
        return sdk.api_call(self.api_key, self.url, self.model, prompt)


    def choose_expert(self, intent:str="", expert_n:int=3)->List[str]:
        '''
        - choose expert
        '''
        with open(self.background_path, "r", encoding="utf-8") as f:
            background_dict = json.load(f)
        expert_list = [value for value in background_dict.keys()] 
        if intent:
            prompt_part = "与用户的意图{intent}，"
            
        else:
            prompt_part = ""
        prompt_expert_list = [{"role": "user", "content": 
f"""请你根据要讨论的topic{self.record['topic']}，{prompt_part}从专家列表{expert_list}中，选择{str(expert_n)}个相关领域的专家,按照以下格式返回：
expert_name1/expert_name2/expert_name3

注意：expert_name1是专家1的名字，expert_name2是专家2的名字，expert_name3是专家3的名字
只按格式生成专家名字，不要生成其他内容。"""}]
    
        except_result = self.call_api(prompt_expert_list)
        except_result_list = except_result.split("/")
        flag = True
        while flag:
            # print(except_result)
            flag = False
            prompt_expert_list.append({"role": "assistant", "content": except_result})
            if len(except_result_list) != expert_n:
                flag = True
            for name in except_result_list:
                if name not in expert_list:
                    # print(name)
                    flag = True
            if flag:
                prompt_expert_list.append({"role": "user", "content": "出现了错误，请重新生成专家名字"})
                except_result = self.call_api(prompt_expert_list)
                except_result_list = except_result.split("/")
            else:
                pass
        self.record["expert_name"] = copy.deepcopy(except_result_list)
        self.record["expert_name"].append("human")
        self.record["order"] = copy.deepcopy(self.record["expert_name"])
        self.record["expert_bk"] = {name:background_dict[name] for name in except_result_list}
        return except_result_list
    
    def augment_background(self, intent:str="")->str:
        '''
        - augment background
        '''
        if intent:
            prompt_part = "与用户的意图:**{intent}** (需要着重考虑用户的意图)"
        else:
            prompt_part = ""
            
        prompt_expert_list = [{"role": "user", "content": 
f"""请你根据要讨论的topic:{self.record['topic']}，{prompt_part}
生成一些内容，增强topic中的信息。
用一段话概括，要有启发性。
"""}]
        result = self.call_api(prompt_expert_list)
        self.record["topic+"] = result
        return result


    def first_round_brainwirte(self, name:str)->None:
        '''
        first round brainwirte
        '''
        if self.contains_chinese_text(name):
            prompt = '''
### 现在正在对**%s**这个话题进行头脑风暴。

### 这是一些关于这个话题的补充
%s

### 请根据你的身份背景，站在你所在领域的视角，参与头脑风暴，并给出你的思考。请用中文回答。

### 生成内容要求简略，用一小段话概括，要有启发性观点，并提出具体的看法或方案.

### 只生成严谨的发言，不要生成其他内容，不需要介绍自己。
    '''%(self.record["topic"], self.record["topic+"])
        else:
            prompt ='''
### Brainstorming on **%s** right now.

### Some additional information about this topic
%s

### According to your background, stand in the perspective of your field, participate in brainstorming, and give your thoughts. **Please answer in English**.

### The generated content should be brief, Sum your viewpoints up in one paragraph (less than 100 words). Please provide **inspiring viewpoints**. And give your specific opinions or solutions.

### Only generate rigorous statements, do not generate other content. Do not introduce yourself.
    '''%(self.record["topic"], self.record["topic+"])
        if name != "human":
            result = self.call_api([{"role": "system", "content": self.record["expert_bk"][name]}
                                                            ,{"role": "user", "content": prompt}])
            self.lock.acquire()
            self.record["round_1"][name] = result
            self.record["paper_%s"%name] = f"- {name}:\n\n{result}\n\n"
            self.lock.release()

        
    def other_round_brainwirte(self, name:str, index:int)->None:
        '''
        other round brainwirte
        '''
        if self.contains_chinese_text(name):
            prompt = '''
%s

### 现在正在对【%s】这个话题进行头脑风暴。以上内容是其他参与者的发言。

### 请根据你的身份背景，站在你所在领域的视角，参与头脑风暴。

### 请仔细阅读其他参与者的发言，根据你的知识背景，继续发展他们的观点。

### 只生成严谨的发言，不要生成其他内容，不要回答自己是谁，请用中文回答。

### 生成内容要求简略，用一小段话概括，要有启发性观点，并提出具体的看法或方案。
    '''%(self.record["paper_%s"%self.record["order"][index]],self.record["topic"])
        else:
            prompt ='''
%s

### Brainstorming on **%s** right now. The above are comments by other participants.

### Participate in brainstorming according to your identity background, standing in the perspective of your field.

### Please carefully read the comments by other participants, based on your knowledge background, continue to develop their viewpoints. Put forward specific ideas and methods.

### The generated content should be brief, Sum your viewpoints up in one paragraph (less than 100 words). No need to introduce yourself.

### Only generate rigorous statements, do not generate other content, please answer in English. 
    '''%(self.record["paper_%s"%self.record["order"][index]],self.record["topic"])
        if name != "human":
            result = self.call_api([{"role": "system", "content": self.record["expert_bk"][name]}
                                                            ,{"role": "user", "content": prompt}])
            self.lock.acquire()
            self.record["round_%d"%self.record["now"]][name] = result
            self.record["paper_%s"%self.record["order"][index]] += f"- {name}:\n\n{result}\n\n"
            self.lock.release()


    def brainwrite(self)->str:
        '''
        brainwrite LLM with human
        '''
        if "round_1" in self.record.keys():
            self.record["round_%d"%self.record["now"]] = {}
            threads = []
            for index, name in enumerate(self.record["expert_name"]):
                thread = threading.Thread(target=self.other_round_brainwirte, args=(name,index))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            # first_person = self.record["order"].pop(0)
            # self.record["order"].append(first_person)

        else:
            self.record["round_1"] = {}
            threads = []
            for name in self.record["expert_name"]:
                thread = threading.Thread(target=self.first_round_brainwirte, args=(name,))
                thread.start()
                threads.append(thread)
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            self.record["now"] = 1



    def human_input_brainwrite(self,human_input:str)->None:
        '''
        human_input_brainwrite input human input in self.record
        '''       
        if self.record["now"] == 1:
            self.record["round_%d"%self.record["now"]]["human"] = human_input
            self.record["now"] += 1
            self.record["paper_human"] = f"- user:\n\n{human_input}\n\n"
        else:
            index_human = self.record["expert_name"].index("human")
            self.record["round_%d"%self.record["now"]]["human"] = human_input
            self.record["now"] += 1
            self.record["paper_%s"%self.record["order"][index_human]] += f"- user:\n\n{human_input}\n\n"
        first_person = self.record["order"].pop(0)
        self.record["order"].append(first_person)

    def paper_content_before_input(self)->str:
        '''
        paper_content_before_input show the paper content human get
        '''
        # if self.record["now"] == 1:
        #     return None
        # else:
        index_human = self.record["expert_name"].index("human")
        return self.record["paper_%s"%self.record["order"][index_human]]

    def record_process(self, path:str)->None:
        '''
        record process in brainwrte
        '''
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(self.record), f, ensure_ascii=False, indent=4)

    def cothinker_summary(self)->None:
        '''
        cothinker to summary the paper human get
        '''
        if "cothinker" not in self.record.keys():
            self.record["cothinker"] = {}
        else:
            pass
        paper_content = self.paper_content_before_input()
        prompt = f'''{paper_content}

以上内容是关于{self.record["topic"]}的讨论，请你分级整理总结。
示例：
- 人工智能的发展历程
    - 早期理论探索
    - 现代广泛应用
- 人工智能在医疗领域的应用
    - 疾病诊断
    - 药物研发
只生成总结的结果不要生成其他内容。
'''
        result = self.call_api([{"role": "user", "content": prompt}])
        self.record["cothinker"]["round_%d"%self.record["now"]] = result
        return result

    def cothinker_interaction(self,human_input:str)->str:
        '''
        - cothinker for human to interacte with llm

        - Multiple rounds of questioning
        '''
        if human_input == None:
            return None
        if "cothinker_%d"%self.record["now"] not in self.record.keys():
            if self.record["now"] == 1:
                prompt = f"""{self.record["topic+"]}

现在正在对{self.record['topic']}这个topic进行讨论
用户基于这个topic和相关背景如上，提出了以下想法：
{human_input}

请你扩展这个想法，要求有启发性。只生成扩展后的想法，不要生成其他内容。
"""
            else:
                prompt = f"""{self.paper_content_before_input()}

现在正在对{self.record['topic']}这个topic进行讨论
用户基于这个topic和相关背景如上，提出了以下想法：
{human_input}

请你扩展这个想法，要求有启发性。只生成扩展后的想法，不要生成其他内容。
"""
        else:
            prompt = human_input

        if "cothinker_%d"%self.record["now"] not in self.record.keys():
            self.record["cothinker_%d"%self.record["now"]] = {}
            self.record["cothinker_%d"%self.record["now"]]["user"] = [prompt]
            result = self.call_api([{"role": "user", "content": prompt}])
            self.record["cothinker_%d"%self.record["now"]]["assistant"] = [result]
            return result
        else:
            prompt_list = []
            for index, item in enumerate(self.record["cothinker_%d"%self.record["now"]]["user"]):
                prompt_list.append({"role": "user", "content": item})
                prompt_list.append({"role": "assistant", "content": self.record["cothinker_%d"%self.record["now"]]["assistant"][index]})
            prompt_list.append({"role": "user", "content": prompt})
            self.record["cothinker_%d"%self.record["now"]]["user"].append(prompt)
            result = self.call_api(prompt_list)
            self.record["cothinker_%d"%self.record["now"]]["assistant"].append(result)
            return result
        
    def get_bk_from_LLM(self,expert_name:str ,prompt_list:List[Dict[str,str]])->str:
        '''
        - get background from llm
        '''
        result = self.call_api(prompt_list)
        self.lock.acquire()
        self.record["expert_bk"][expert_name] = result
        self.lock.release()
        
    def choose_expert_without_human(self, intent:str="", expert_n:int=3)->List[str]:
        '''
        - choose expert without human
        
        - get expert background by llm
        '''
        if intent:
            prompt_part = "与用户的意图{intent}，"
            
        else:
            prompt_part = ""
        prompt_expert_list = [{"role": "user", "content": 
f"""请你根据要讨论的topic{self.record['topic']}，{prompt_part}，
选择{str(expert_n)}个相关领域的真实存在的知名中外专家，按照以下格式返回：
专家1/专家2/专家3

eg：华罗庚/Gaussian/陈景润
只按格式生成专家名字，不要生成其他内容。"""}]
    
        except_result = self.call_api(prompt_expert_list)
        except_result_list = except_result.split("/")
        flag = True
        while flag:
            flag = False
            prompt_expert_list.append({"role": "assistant", "content": except_result})
            if len(except_result_list) != expert_n:
                flag = True
            if flag:
                prompt_expert_list.append({"role": "user", "content": "出现了错误，请按照“专家1/专家2/专家3”这种格式生成。"})
                except_result = self.call_api(prompt_expert_list)
                except_result_list = except_result.split("/")
            else:
                pass
        self.record["expert_name"] = copy.deepcopy(except_result_list)
        self.record["order"] = copy.deepcopy(self.record["expert_name"])
        self.record["expert_bk"] = {}
        threads = []
        for name in self.record["expert_name"]:
            if self.contains_chinese_text(name):
                prompt = f"""### 用中文写一段prompt 
### 用来提示大模型 扮演**{name}**，参与**{self.record['topic']}**的讨论
### 简单介绍一下其背景与特长（要求简短）
### prompt中要包含提示大模型进行身份扮演的语句
### 请使用 # 与 - 等符号对段落进行分割
"""
            else:
                prompt = f"""### 用英文写一段prompt 
### 用来提示大模型 扮演**{name}**，参与**{self.record['topic']}**的讨论
### 简单介绍一下其背景与特长（要求简短）
### prompt中要包含提示大模型进行身份扮演的语句
### 请使用 # - 等符号对段落进行分割
"""
            prompt_for_expert_bk = [{"role": "user", "content": prompt}]
            thread = threading.Thread(target=self.get_bk_from_LLM, args=(name,prompt_for_expert_bk))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return except_result_list
    
    def brainwrite_without_human(self)->str:
        '''
        brainwrite LLM without human
        '''
        if "round_1" in self.record.keys():
            self.record["round_%d"%self.record["now"]] = {}
            first_person = self.record["order"].pop(0)
            self.record["order"].append(first_person)
            threads = []
            for index, name in enumerate(self.record["expert_name"]):
                thread = threading.Thread(target=self.other_round_brainwirte, args=(name,index))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            self.record["now"] += 1

        else:
            self.record["round_1"] = {}
            self.record["now"] = 1
            threads = []
            for name in self.record["expert_name"]:
                thread = threading.Thread(target=self.first_round_brainwirte, args=(name,))
                thread.start()
                threads.append(thread)
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            self.record["now"] += 1
            

if __name__ == "__main__":
    url = "https://open.bigmodel.cn/api/paas/v4/"
    model = "glm-4-flash"
