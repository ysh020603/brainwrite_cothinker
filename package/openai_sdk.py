from openai import OpenAI 
from typing import Dict, List, Literal

def api_call(key:str, url:str, model:str, prompt:list[dict[str,str]], temperature: float = 0.9, top_p: float = 0.7) -> str:
    '''
    使用openai库调用api
    - spark调用api_key的填写格式 控制台获取key和secret拼接,中间用:分割key:secret
    - 智谱的调用只需要复制api_key即可,中间会有一个.
    - moonshot公司直接使用openai的api调用库
    '''
    client = OpenAI(
        api_key=key,
        base_url=url
    ) 

    completion = client.chat.completions.create(
        model=model,  
        messages=prompt,
        top_p=top_p,
        temperature=temperature
     ) 
    
    return completion.choices[0].message.content

