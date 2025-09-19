# utils_llm.py
# 同济子豪兄 2024-5-22
# 调用大语言模型API

print('导入大模型API模块')


import os

import qianfan
def llm_qianfan(PROMPT='你好，你是谁？'):
    '''
    百度智能云千帆大模型平台API
    '''
    
    # 传入 ACCESS_KEY 和 SECRET_KEY
    os.environ["QIANFAN_ACCESS_KEY"] = QIANFAN_ACCESS_KEY
    os.environ["QIANFAN_SECRET_KEY"] = QIANFAN_SECRET_KEY
    
    # 选择大语言模型
    MODEL = "ERNIE-Bot-4"
    # MODEL = "ERNIE Speed"
    # MODEL = "ERNIE-Lite-8K"
    # MODEL = 'ERNIE-Tiny-8K'

    chat_comp = qianfan.ChatCompletion(model=MODEL)
    
    # 输入给大模型
    resp = chat_comp.do(
        messages=[{"role": "user", "content": PROMPT}], 
        top_p=0.8, 
        temperature=0.3, 
        penalty_score=1.0
    )
    
    response = resp["result"]
    return response

import openai
from openai import OpenAI
from API_KEY import *

def llm_yi(message):
    '''
    零一万物大模型API
    '''
    
    API_BASE = "https://api.lingyiwanwu.com/v1"
    API_KEY = YI_KEY

    MODEL = 'yi-large'
    # MODEL = 'yi-medium'
    # MODEL = 'yi-spark'
    
    # 访问大模型API
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    completion = client.chat.completions.create(model=MODEL, messages= message)
    result = completion.choices[0].message.content.strip()
    return result
    
# 轻量日志工具
def _append_log(path: str, text: str):
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'a') as f:
            f.write(text + '\n')
    except Exception as _e:
        print('写日志失败: {}'.format(_e))

def private_llm(message):
    '''
    私有化部署的OpenAI格式文本模型API
    增加最多3次重试（指数退避：0.5s, 1s, 2s），全部失败后抛出异常。
    '''
    from time import time as _now, sleep
    log_path = 'temp/private_llm.log'

    # 记录入参与模型信息
    try:
        import json
        messages_preview = json.dumps(message, ensure_ascii=False)
    except Exception:
        messages_preview = str(message)
    base_url = PRIVATE_BASE_URL
    model = PRIVATE_LLM_MODEL
    print('REQ base_url={} model={} messages={}'.format(base_url, model, messages_preview))

    last_err = None
    for attempt in range(1, 4):  # 1..3
        start_ts = _now()
        try:
            client = OpenAI(
                api_key=PRIVATE_API_KEY, 
                base_url=base_url
            )
            completion = client.chat.completions.create(
                model=model, 
                messages=message
            )
            latency = _now() - start_ts
            # 原始返回尽量保持完整，但避免过大
            try:
                import json
                raw_text = json.dumps(completion.model_dump(), ensure_ascii=False)
            except Exception:
                raw_text = str(completion)
            if len(raw_text) > 4000:
                raw_text = raw_text[:4000] + '...<truncated>'
            print('RES attempt={} latency={:.2f}s raw={}'.format(attempt, latency, raw_text))

            result = completion.choices[0].message.content.strip()
            print('OUT attempt={} text={}'.format(attempt, result))
            return result
        except Exception as e:
            latency = _now() - start_ts
            last_err = e
            print('ERR attempt={} latency={:.2f}s err={}'.format(attempt, latency, str(e)))
            # 指数退避
            if attempt < 3:
                backoff = 0.5 * (2 ** (attempt - 1))  # 0.5, 1.0
                try:
                    sleep(backoff)
                except Exception:
                    pass
            else:
                break
    # 全部失败
    raise last_err

# ========== 私有模型连通性测试 ==========

def test_private_llm(prompt: str = '测试一下你是否在线，请用一句中文回答，附带模型名') -> str:
    '''
    连通性与权限自检：向私有模型发送一条简单消息，返回模型回复文本。
    成功：返回文本；失败：抛出异常，便于上层捕获并打印报错。
    '''
    # 构造最小 messages（符合 OpenAI Chat Completions 格式）
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    # 透传到现有的私有模型调用逻辑
    return private_llm(messages)

if __name__ == '__main__':
    # 命令行直接运行自检
    import sys
    prompt = '测试一下你是否在线，请用一句中文回答，附带模型名'
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
    print('私有模型自检中...')
    print('BASE_URL = {}'.format(PRIVATE_BASE_URL))
    print('MODEL    = {}'.format(PRIVATE_LLM_MODEL))
    try:
        result = test_private_llm(prompt)
        print('调用成功：\n{}'.format(result))
    except Exception as e:
        print('调用失败：{}'.format(e))
        raise
