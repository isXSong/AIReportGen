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
    failed_results = {}
    #处理ItemResults及其下的各审查Task
    for article, content in item_results.items():
        check_results    = content.get("CheckResults", [])
        natural_language = content.get("NaturalLanguage")
        fail_tasks = []
        for task in check_results:
            if not (task.get("Pass") or task.get("TaskType")  == "CheckValid"):
                idset = task.get("IdSet")
                del task["TaskType"], task["Pass"], task["ifPass"], task["ErrorType"]
                del task["errValue"], task["errCateCount"], task["Reason"], task["IdSet"]
                eleminfo = []
                for id in idset:
                    elem = element_info.get(id)
                    info = "[" + id + "]" + elem.get("CN") + "--" + elem.get("EN")
                    eleminfo.append(info)
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
    if '#####' in text:
        parts = text.split('#####')
        json_str = parts[1].strip()
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