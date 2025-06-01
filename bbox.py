#如果确有不处理包围盒信息的需求，将此变量设为False
#一般情况下，不必修改此开关，即便json数据中没有提供构件包围盒信息，也不会出现运行异常
handling_box_switch = True


class AreaDivider:
	'''
	区域划分器，用于封装图纸全局范围和区域划分
	'''
	xmin: int
	xmax: int
	ymin: int
	ymax: int
	zmin: int
	zmax: int
	valid_flag: bool	#至少要提供一个构件的包围盒

	def __init__(self):
		self.xmin = 0
		self.ymin = 0
		self.zmin = 0 
		self.xmax = 1e6
		self.ymax = 1e6
		self.zmax = 1e6
		self.valid_flag = False


	def add_box(self, xi , yi, zi, xa, ya, za)-> None:
		'''
		AreaDivider不会储存构件box，但需要遍历添加所有box，以确定全局范围
		'''
		self.xmin = min(self.xmin, xi)
		self.xmax = max(self.xmax, xa)
		self.ymin = min(self.ymin, yi)
		self.ymax = max(self.ymax, ya)
		self.zmin = min(self.zmin, zi)
		self.zmax = max(self.zmax, za)
		self.valid_flag = True


	def set_area_division(self) -> None:
		'''
		标志着所有box信息输入完毕，确定全局范围和区域划分
		'''
		if not self.valid_flag: return
		self.mid_left 	= (2*self.xmin + self.xmax) / 3
		self.mid_right 	= (self.xmin + 2*self.xmax) / 3
		self.mid_top 	= (2*self.ymin + self.ymax) / 3
		self.mid_bottom = (self.ymin + 2*self.ymax) / 3


	def get_pos_info(self, x, y, z) -> str:
		'''
		根据坐标返回其在图纸中的位置描述描述
		'''
		if not self.valid_flag: return '无位置信息'
		exact_pos = f"(x={x}, y={y}, z={z})"
		if not (self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax):
			return "外部" + exact_pos
		
		x_info, y_info, area_info = '', '', ''
		if 	 x <= self.mid_left: 	x_info = '左'
		elif x >= self.mid_right: 	x_info = '右'
		else: 						x_info = '中'
		if   y <= self.mid_bottom: 	y_info = '下'
		elif y >= self.mid_top: 	y_info = '上'
		else: 						y_info = '中'
		if   x_info == y_info: 		area_info = '中部'
		else: 						area_info = x_info + y_info
		
		return area_info + exact_pos
	

	def get_pos_info_by_elem(self, elem: dict) -> str:
		'''
		根据构件返回其在图纸中的位置描述描述
		'''
		if elem is None or 'BBox' not in elem: return '无位置信息'
		bbox = [int(val) for val in elem['BBox'].split(',')]
		pos = [(bbox[i] + bbox[i+3]) / 2 for i in range(0, 3)]
		return self.get_pos_info(*pos)


def get_drawing_AreaDivider(elems: dict) -> AreaDivider:
	'''
	根据图纸中构件的json数据，返回一个AreaDivider对象
	'''
	ad = AreaDivider()
	if not handling_box_switch:
		return ad		#此时的ad的valid_flag为False
	for id, elem in elems.items():
		if 'BBox' not in elem: continue
		bbox = [int(val) for val in elem['BBox'].split(',')]
		ad.add_box(*bbox)
	ad.set_area_division()
	return ad