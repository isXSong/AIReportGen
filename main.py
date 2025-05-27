import json
import requests
from ops import *
from llm_config import *
from visualize import visualize_bounding_boxes

'''
@author: isXSong
@date: 2025-05-18
@description:
'''

default_llm = modules['tuzhi-70B']				#默认模型选择，参看llm_config.py
origin_jsonfile = "./1/report1_new.json"				#原始json审查数据
save_reasonal_jsonfile = "./1/reasonal1_new.json"		#保存整合了原因的json审查数据，设置为空字符串则不保存
save_reportfile = "./1/report1_new.txt"				#保存自然语言报告
stream_output = True	#是否同时流式输出到控制台

def get_llm_response(messages, llm = default_llm) -> str:
	'''
	向llm发送询问，获取结果
	:param llm: llm的配置，字典类型，在llm_config.py中有预设
	:param messages: 询问的信息，列表类型，每个元素是一个字典，包含role和content
	:return: llm回复的content，字符串类型
	'''
	url = llm['url']
	headers = {
        "Content-Type": "application/json",
		'authorization': f'Bearer {llm['api_key']}'
    }
    
	data = {
        "model": llm['model'],
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
    }
	full_response = ''
	try:
		with requests.post(
            url,
            headers=headers,
            json=data,
            stream=True
        ) as response:
			response.raise_for_status()
            
			for line in response.iter_lines():
				if line:
					decoded_line = line.decode('utf-8')
					if decoded_line.startswith("data: "):
						chunk = decoded_line[6:]
						if chunk == "[DONE]":
							break
						try:
							chunk_json = json.loads(chunk)
							content = chunk_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
							if content:
								if stream_output:
									print(content, end="", flush=True)
								full_response += content
						except json.JSONDecodeError:
							print(f"解析错误: {chunk}")
	except requests.exceptions.RequestException as e:
		print(f"请求出错: {e}")
	finally:
		return str(full_response)
	

def generate_reason_explanation(jsondata) -> dict:
	'''
	为json审查数据中的每个task生成自然语言解释不通过的原因
	:param jsondata: 过滤后的json审查数据
	:return: 整合reason后的jsondata
	'''
	user_msg = json.dumps(jsondata, ensure_ascii=False, indent=4)
	msg = [
		{"role": "system", "content" : prompt_GetReason},
		{"role": "user", "content": prompt_GetReason + "\n数据如下：" + user_msg}
	]
	resp = get_llm_response(msg)
	return embed_reason_into_data(resp, jsondata)
	

def generate_report(jsondata) -> str:
	'''
	为json审查数据生成自然语言报告
	:param jsondata: 过滤后的json审查数据
	:return: 自然语言报告
	'''
	user_msg = json.dumps(jsondata, ensure_ascii=False, indent=4)
	sys_msg = prompt_GenerateReport
	msg = [
		{"role": "system", "content" : sys_msg},
		{"role": "user", "content": report_format},
		{"role": "user", "content": user_msg}
	]
	resp = get_llm_response(msg)
	return resp.split('</think>')[1]

if __name__ == "__main__":
	#载入并过滤原始json数据
	jsondata = load_and_filter_jsondata(origin_jsonfile)
	#生成reason并整合到json数据中
	jsondata = generate_reason_explanation(jsondata)
	if save_reasonal_jsonfile != '':
		with open(save_reasonal_jsonfile, 'w', encoding='utf-8') as f:
			json.dump(jsondata, f, ensure_ascii=False, indent=4)
	#生成自然语言报告
	report = generate_report(jsondata)
	with open(save_reportfile, 'w', encoding='utf-8') as f:
		f.write(report)