import json
import os
import re

def load_and_filter_jsondata(jsonfile: str) -> dict:
    '''
    从json文件中读取审查结果数据，并过滤掉通过审查的结果和部分不需要的数据
    :param jsonfile: json文件路径
    :return: 过滤后的json数据，字典
    '''
    with open(jsonfile, 'r', encoding='utf-8') as jf:
        json_data = json.load(jf)
    id_count = 0
    #读取需要的json一级条目
    item_results    = json_data["ItemResults"]
    summary_for_snl = json_data["consistencySummarySimplified"]
    summary_for_art = json_data["consistencySummarySimplifiedForArticle"]
    element_info    = json_data["elementsSemanticInfo"]
    
    #获取整个建筑的最大包围盒
    min_info = [float('inf'), float('inf'), float('inf')]
    max_info = [0, 0, 0]
    for id, elem in element_info.items():
        if 'BBox' in elem:
            box = [ int(val) for val in elem['BBox'].split(',')]
            min_info = [min(min_info[i], box[i]) for i in range(3)]
            max_info = [max(max_info[i], box[i+3]) for i in range(3)]
    bounding_info = {
        "x": {'lleft'  : min_info[0],  'left'  : (2/3)*min_info[0] + (1/3)*max_info[0],
              'rright' : max_info[0],  'right' : (1/3)*min_info[0] + (2/3)*max_info[0]}, 
        "y": {'ffront' : min_info[1],  'front' : (2/3)*min_info[1] + (1/3)*max_info[1],
              'bback'  : max_info[1],  'back'  : (1/3)*min_info[1] + (2/3)*max_info[1]},
        "z": {} #unused
        }
    
    #处理ItemResults及其下的各审查Task
    failed_results = {}
    for article, content in item_results.items():
        check_results    = content.get("CheckResults", [])
        natural_language = content.get("NaturalLanguage")
        fail_tasks = []
        for task in check_results:
            if not (task.get("Pass") or task.get("TaskType")  == "CheckValid"):
                idset = task.get("IdSet")
                del task["TaskType"], task["Pass"], task["ErrorType"]
                del task["errValue"], task["errCateCount"], task["Reason"], task["IdSet"]
                if 'ifPass' in task:  del task['ifPass']
                eleminfo = {}
                for id in idset:
                    elem = element_info.get(id)
                    info = '[' + id + ']'
                    if 'BBox' in elem:
                        box = [ int(val) for val in elem['BBox'].split(',')]
                        pos = [ (box[i] + box[i+3]) / 2 for i in range(0, 3) ]
                        info += get_position_info(pos, bounding_info)
                    else:
                        info += "无定位"
                    type = elem.get("CN") + "-" + elem.get("EN")
                    eleminfo[info] = type
                task["ElementInfo"] = eleminfo
                id_count += 1
                task["id"] = id_count
                fail_tasks.append(task)
        if fail_tasks:
            failed_results[article] = {"CheckResults": fail_tasks, "NaturalLanguage": natural_language}
    #重新组合，返回结果
    return {"FailedResults": failed_results, "consistencySummarySimplified": summary_for_snl, "consistencySummarySimplifiedForArticle": summary_for_art}


def extract_json_from_resp(text) -> dict:
    '''
    从模型输出中提取json部分
    '''
    if '</think>' in text:
        text = text.split('</think>')[1]
        if '```json' in text:
            text = text.split('```json')[1]
            if '```' in text:
                json_str = text[1].split('```')[0]
            else:
                json_str = text[1]
            json_str.strip()
            json_str = re.findall(r'(\{.*?\})', text, re.DOTALL)[0]
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError:
        raise Exception(f"生成Reason解析失败，可能是模型未按指定格式给出输出")


def embed_reason_into_data(reason: str, jsondata) :
    '''
    将模型生成的reason嵌入到jsondata中
    :param reason: 模型生成的包含reason的文本
    '''
    reason_dict = extract_json_from_resp(reason)
    failed_results = jsondata["FailedResults"]
    for article, content in failed_results.items():
        check_results = content.get("CheckResults")
        for task in check_results:
            id = task.get("id")
            reason = reason_dict.get(str(id))
            task["Reason"] = reason
            del task["id"]
        content["CheckResults"] = check_results
    jsondata["FailedResults"] = failed_results
    return jsondata


def get_position_info(pos: list, info: dict) -> str:
    '''
    根据包围盒信息，获取元素在图纸中的方位描述
    :param pos: 构件中心点坐标，列表[x, y, z]
    :param info: 图纸有效范围的信息
    :return: 方位描述，字符串
    '''
    coord = f"(x={pos[0]}, y={pos[1]}, z={pos[2]})"
    if not (info['x']['lleft'] <= pos[0] <= info['x']['rright'] and info['y']['ffront'] <= pos[1] <= info['y']['bback']):
        return "外部" + coord
    
    x_str, y_str, pos_str = '', '', ''
    if pos[0] <= info['x']['left']:     x_str = '左'
    elif pos[0] >= info['x']['right']:  x_str = '右'
    else:                               x_str = '中'
    if pos[1] <= info['y']['front']:    y_str = '前'
    elif pos[1] >= info['y']['back']:   y_str = '后'
    else:                               y_str = '中'
    if x_str == y_str :                 pos_str = '中心'
    else:                               pos_str = x_str + y_str

    return pos_str + coord