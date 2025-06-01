import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import json

highlight_unpassed = True
include_BiaoQian = True

def get_boxes_from_json(jsonfile: str)-> dict:
    #从json读取数据
    with open(jsonfile, 'r', encoding='utf-8') as jf:
        json_data = json.load(jf)
    element_info = json_data["elementsSemanticInfo"]

    #获取整个建筑的最大包围盒
    boxes = {}
    min_info = [float('inf'), float('inf'), float('inf')]
    max_info = [0, 0, 0]
    for id, elem in element_info.items():
        if 'BBox' in elem and (include_BiaoQian or elem['CN'] != '标签'):
            box = [ int(val) for val in elem['BBox'].split(',')]
            box.append(True)
            min_info = [min(min_info[i], box[i]) for i in range(3)]
            max_info = [max(max_info[i], box[i+3]) for i in range(3)]
            boxes[id] = box
    max_box = min_info + max_info
    
    if highlight_unpassed:
        item_results = json_data["ItemResults"]
        for key, value in item_results.items():
            check_results = value.get("CheckResults")
            for task in check_results:
                if not (task.get("Pass") or task.get("TaskType")  == "CheckValid"):
                    idset = task.get("IdSet")
                    for id in idset:
                            elem = element_info.get(id)
                            if id in boxes:
                                boxes[id][6] = False
	
    return boxes, max_box

def draw_boxes(boxes: dict, max_box: list):
    fig, ax = plt.subplots()
    ax.set_xlim(0, max_box[3]+1000)
    ax.set_ylim(0, max_box[4]+1000)
    # rect_max = Rectangle((max_box[0], max_box[1]), max_box[3]-max_box[0], max_box[4] - max_box[1]
    #                      , linewidth=1, edgecolor='black', facecolor='none')
    # ax.add_patch(rect_max)
    format_t = {'linewidth' : 1, 'edgecolor': 'black', 'facecolor': 'none', 'alpha': 0.2}
    format_f = {'linewidth' : 1, 'edgecolor': 'red', 'facecolor': 'none', 'alpha': 0.8}
    for id, box in boxes.items():
        width = box[3] - box[0]
        height = box[4] - box[1]
        if box[6]:
            rect = Rectangle((box[0], box[1]), width, height, **format_t)
        else:
            rect = Rectangle((box[0], box[1]), width, height, **format_f)
        ax.add_patch(rect)
    plt.show()
    
def visualize_bounding_boxes(jsonfile: str):
    boxes, max_box = get_boxes_from_json(jsonfile)
    draw_boxes(boxes, max_box)

if __name__ == '__main__':
    visualize_bounding_boxes('./1/report1_new.json')