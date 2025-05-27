thudpsk = {
	'url' : 'https://madmodel.cs.tsinghua.edu.cn/v1/chat/completions',
	'api_key' : 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2RlIjoiMTAyNyIsImlhdCI6MTc0NzI5MTE2OCwiZXhwIjoxNzQ3MzEyNzY4fQ.kM5fYHSyFu4dfa0HtbscNLbPB2OPsFWQlcGztx_LrMA'
	#'models' : ['DeepSeek-R1-Distill-32B', 'DeepSeek-R1-671B']
}

dpsk = {
	'url' : 'https://api.deepseek.com/v1/chat/completions',
	'api_key' : 'sk-71b919bbc51040fc957c3ba95041835e'
	#'models' : ['deepseek-chat', 'deepseek-reasoner']
}

tuzhi_dpsk = {
	'url' : 'https://llm.tuzhi.ai:7443/api/chat/completions',
	'api_key' : 'sk-7d957546cbf14e0c8f0dd3b2345de409'
}

modules = {
	"thudpsk-32B" : thudpsk | {'model' : 'DeepSeek-R1-Distill-32B'},
	"thudpsk-671B" : thudpsk | {'model' : 'DeepSeek-R1-671B'},
	"dpsk-chat" : dpsk | {'model' : 'deepseek-chat'},
	"dpsk-reasoner" : dpsk | {'model' : 'deepseek-reasoner'},
	"tuzhi-70B" : tuzhi_dpsk | {'model' : 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B'}
}

prompt_GetReason = '''
数据说明：用户将会提供一段Json数据，这段数据存储了对某建筑按条文进行消防建筑规范机器审查的不通过的反馈，其中的'FailedResults'对象是你要关注的。在'FailedResult'中的每个键是一个条文的名，而在其对应的值中：
- 'Nautural Language'是该条文的原文
- 'CheckResults'是一个数组用来存储通过SNL对该条文审查的结果（只包括未通过的），其中的每个对象称为一个'SNLTask'，其中的：
    - 'id'按顺序唯一标识了该SNLTask
	- 'SNL'代表用于审查的SNL语句，是一种机器条件判断语句
	- 'ElementInfo'是该条审查中出问题的构件，以键值对的形式存储了构件的id、位置、类型、名称
	- 'errPairValue'存储了出错构件对应的出错属性值（例如梁A01规范长度为1m，但实际长度为0.5m，则此处记'A01 0.5m'）。
需求说明：请你根据这些信息，为每个'SNLTask'生成一段简明扼要的自然语言(约40-100字)，面向用户直接说明审查不通过的原因，简短易懂为要，不要使用太过专业、晦涩的术语，不要引用构件编号（因为编号不是面向用户的），不要使用冗余的语气修饰和措辞。一些正向的例子比如'二楼厨房未按规定设置防火门'，'营业厅疏散通道的宽度为0.5m，小于规范要求的1.0m'，'歌舞厅作为人员密集的公共场所，疏散门不应设置门槛'，'餐馆面积大于1000m2，按规定其烹饪操作间的排油烟罩需要设置自动灭火装置。'等。
格式说明：为了方便程序识别提取，请以json格式输出一个字典，json中的每个键是'SNLTask'的'id'，值是你为该'SNLTask'生成的错误原因描述, 并确保json数据前有‘```json’标识
'''
##例如'二楼厨房未按规定设置防火门'，'营业厅的疏散通道A01宽度为0.5m，小于规范要求的1.0m'，'人员密集的公共场所、观众厅的疏散门不应设置门槛，其净宽度不应小于1．40m'等，不要使用太过专业、晦涩或冗长的术语，不要添加'经核查/按第xx.xx条规定'等冗余措辞

prompt_GenerateReport = '''
**数据说明**：用户将会提供一段Json数据，这段数据存储了某建筑的消防审查数据，其中包括三个对象：FailedResults'存储审查的结果，'consistencySummarySimplified'对象和'consistencySummarySimplifiedForArticle'是不同尺度下对通过率的机器统计。
'FailedResult'是一个词典，其中每个键是一个条文的名，而其对应的值：
- 'Nautural Language'是该条文的原文
- 'CheckResults'是一个数组用来存储通过SNL对该条文审查的结果（只包括未通过的），其中的每个对象称为一个'SNLTask'，其中的：
    - 'Reanson'通过自然语言描述了审查不通过的原因，供你做主要参考
	- 'ElementInfo'是该条审查中出问题的构件，以键值对的形式存储了构件的id、位置、类型、名称
	- 'SNL'代表用于审查的SNL语句，'errPairValue'存储了出错的属性值。这些信息在'Reason'中理应包含，但有时也可能缺失。
'consistencySummarySimplified'对象存储了按SNL语句判断层次的通过率，'consistencySummarySimplifiedForArticle'对象存储了条文层次的通过率，其中：
- 'summary_str'是自然语言描述的对统计数据的总结，供你做主要参考
- 其他条目在'summary_str'中都有体现，一般无需关注
**需求说明**：用户将会提供一份报告的格式，请你根据提供的json信息和审查报告格式，生成一份的审查报告
'''

report_format = '''
以下是报告格式：
**审查情况总述**：{data_description}
**分类展示审查结果**：
类型（可自行按位置或错误类型分类、可以合并必要的相似项）：{error_type}
-{错误}：{错误描述}
	>> 构件名称：...
	>> 构件位置：...
	>> 涉及条文名称：....
	>> 原文选摘：简短即可，但必须严格忠于原文，只摘录条规原文中和错误最相关的部分，容许用省略号跳跃不太相干的部分
**整改建议**：{review_summary}
'''