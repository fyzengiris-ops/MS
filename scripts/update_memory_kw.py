# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
jp = root / "data" / "questions.json"
data = json.loads(jp.read_text(encoding="utf-8"))

by_id = {x["id"]: x for x in data["items"]}

by_id["Q28_55"]["memoryKeywords"] = ["运动", "跳舞"]

by_id["Q28_56"]["memoryKeywords"] = [
    {
        "title": "优点",
        "points": [
            {"label": "工作角度", "text": "能承担责任和抗事"},
            {"label": "成长角度", "text": "自驱力"},
        ],
    },
    {
        "title": "缺点",
        "points": [
            {"label": "工作上", "text": "对于专业设计的坚持边界有继续加强的空间"},
            {"label": "个人性格", "text": "对设计的审美会比较扣细节，会略微吹毛求疵"},
        ],
    },
]

by_id["Q28_57"]["memoryKeywords"] = [
    {
        "title": "工作中",
        "points": [
            {"text": "靠谱"},
            {"text": "情绪稳定"},
        ],
    },
    {
        "title": "生活中",
        "points": [
            {"text": "自律"},
        ],
    },
]

by_id["Q17_58"]["memoryKeywords"] = [
    {
        "title": "最终目标",
        "points": [
            {"text": "高级产品经理，产品总监成长"},
        ],
    },
    {
        "title": "3-5年的规划",
        "points": [
            {"text": "深化AI产品能力，持续完善个人职场竞争力"},
            {"text": "扩大对产品价值和商业结果负责的责任范围"},
        ],
    },
]

by_id["Q24_47"]["memoryKeywords"] = ["沟通能够直接、坦诚的"]

by_id["Q23_46"]["memoryKeywords"] = [
    {
        "title": "持续的输入",
        "points": [
            {"text": "huggingface"},
        ],
    },
    {
        "title": "判断",
        "points": [
            {"text": "能力的变化"},
            {"text": "相关性"},
        ],
    },
    {
        "title": "研究",
        "points": [
            {"text": "解决了什么问题"},
            {"text": "核心机制是什么"},
            {"text": "怎么应用"},
            {"text": "商业价值在哪里"},
        ],
    },
]

by_id["Q22_45"]["memoryKeywords"] = [
    {
        "title": "日常的思考和复盘",
        "points": [
            {"label": "GPT｜工作问题分析", "text": "视角和场景的拓展"},
            {"label": "GPT｜日报月度复盘", "text": "提效，聚焦核心问题点"},
        ],
    },
    {
        "title": "模型能力验证",
        "points": [
            {"label": "阶段性使用", "text": "豆包、Qwen3.7-puls、deepseek"},
        ],
    },
]

by_id["Q17_41"]["memoryKeywords"] = [
    "薪资不符合目前市场上对于5年产品工作经验的正常薪资范围"
]

by_id["Q17_37"]["memoryKeywords"] = [
    {
        "title": "项目",
        "points": [
            {"text": "接送系统"},
        ],
    },
    {
        "title": "难的原因",
        "points": [
            {"label": "项目本身", "text": "协作复杂、角色多、业务逻辑复杂"},
            {"label": "自身情况", "text": "首次负责0-1系统（分析不够深入、产品设计来回打磨）"},
        ],
    },
    {
        "title": "项目结果",
        "points": [
            {"text": "一个月完成四个终端的方案设计，累计开发3个半月时间，达到可验收状态"},
        ],
    },
    {
        "title": "复盘",
        "points": [
            {"label": "好的地方", "text": "高保真方案、态度好，及时反馈和调整"},
            {"label": "不好的地方｜分析", "text": "缺少真实用户反馈"},
            {"label": "不好的地方｜方案", "text": "思考深度不够"},
        ],
    },
    {
        "title": "后续调整",
        "points": [
            {"text": "定期学习"},
        ],
    },
    {
        "title": "重来一次",
        "points": [
            {"text": "到校调研交流、方案设计，结合终端特性"},
        ],
    },
    {
        "title": "可优化点",
        "points": [
            {"label": "对外", "text": "班级屏学生放学"},
            {"label": "对内", "text": "学生信息维护"},
        ],
    },
]

by_id["Q17_38"]["memoryKeywords"] = [
    {
        "title": "方式",
        "points": [
            {"text": "了解缘由，评估风险"},
        ],
    },
    {
        "title": "结果",
        "points": [
            {"text": "尊重领导的决定"},
        ],
    },
    {
        "title": "理由",
        "points": [
            {
                "text": "即便是领导，做事，肯定也是综合考虑多个维度的因素后，奔着把事做好的目标去做的",
            },
        ],
    },
    {
        "title": "举例",
        "points": [
            {"text": "自适应策略出题"},
        ],
    },
]

by_id["Q17_39"]["memoryKeywords"] = [
    {
        "title": "原则",
        "points": [
            {"text": "业务阶段性需求，还是硬性要求"},
        ],
    },
    {
        "title": "阶段性需要",
        "points": [
            {"text": "和团队一条心，保证业务目标需要（排课系统）"},
        ],
    },
    {
        "title": "硬性要求",
        "points": [
            {"label": "一周一两天", "text": "遵守制度"},
            {"label": "每天加班", "text": "不能接受"},
        ],
    },
]

by_id["Q17_40"]["memoryKeywords"] = [
    {
        "title": "核心",
        "points": [
            {"text": "保持可控"},
        ],
    },
    {
        "title": "方式",
        "points": [
            {"text": "明确目标、排好优先级、对齐关键节点、及时同步风险和进度"},
        ],
    },
    {
        "title": "举例",
        "points": [
            {"label": "作业批注", "text": "需求定位错误，重新梳理需求"},
            {"label": "OCR", "text": "方案不完善，开发催促，需要推进开发"},
        ],
    },
    {
        "title": "复盘",
        "points": [
            {"text": "无时间了解背景的需求"},
            {"text": "有时间了解背景的需求"},
        ],
    },
]

by_id["Q19_42"]["memoryKeywords"] = [
    {
        "title": "稳定使用的",
        "points": [
            {"text": "Cursor、Codex"},
        ],
    },
    {
        "title": "方案阶段",
        "points": [
            {"text": "重点把控设计细节，确保传达出产品思想"},
        ],
    },
    {
        "title": "PRD阶段｜自建Skill",
        "points": [
            {
                "text": "保证逻辑完整性、准确性、易读性，以及AI开发的高效性",
            },
            {"label": "①", "text": "UI元素的完整性"},
            {"label": "②", "text": "逻辑完整性"},
            {"label": "③", "text": "沉淀页面已实现逻辑"},
            {"label": "④", "text": "自动补全页面未实现逻辑"},
            {"label": "⑤", "text": "产品审核"},
            {"label": "⑥", "text": "生成md文档"},
        ],
    },
]

by_id["Q20_43"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "都是解决不同问题的能力组件"},
            {"label": "RAG", "text": "解决专业性问题"},
            {"label": "工作流", "text": "解决稳定性问题"},
            {"label": "Agent", "text": "解决需要动态判断下一步输出什么内容"},
        ],
    },
    {
        "title": "实际使用",
        "points": [
            {"text": "目标以及完成目标所需要处理的事项"},
        ],
    },
    {
        "title": "最终判断",
        "points": [
            {"text": "成本、复杂度"},
        ],
    },
]

by_id["Q16_36"]["memoryKeywords"] = [
    {
        "title": "行为",
        "points": [
            {"text": "基于问题根因和表现，AI创建问题，线下收集问题"},
        ],
    },
    {
        "title": "结果",
        "points": [
            {"text": "92%的准确率，8%的错误率（语序、特殊符号、不正确的拼音）"},
        ],
    },
    {
        "title": "决策",
        "points": [
            {"text": "8%不处理，考虑ROI"},
        ],
    },
]

by_id["Q15_35"]["memoryKeywords"] = [
    {
        "title": "核心要素",
        "points": [
            {"label": "RAG", "text": "文档质量、切片结构、检索召回"},
            {"label": "Prompt", "text": "角色、场景、任务边界、兜底逻辑、闭环"},
        ],
    },
    {
        "title": "不适用场景",
        "points": [
            {"label": "RAG", "text": "时效性强的信息"},
            {"label": "Prompt", "text": "多场景"},
        ],
    },
]

by_id["Q14_34"]["memoryKeywords"] = [
    {
        "title": "异常场景的确认",
        "points": [
            {"text": "线上历史数据、线下真实反馈、技术支持、开发&测试"},
        ],
    },
    {
        "title": "支持处理的问题类型",
        "points": [
            {"text": "网络、功能设置"},
        ],
    },
    {
        "title": "解决方案的形成",
        "points": [
            {"text": "完整的业务链路"},
            {"text": "AI可参与的环节（口语转译、信息反馈）"},
        ],
    },
]

by_id["Q13_32"]["memoryKeywords"] = [
    {
        "title": "coze搭建智能体",
        "points": [
            {"text": "验证复杂度、稳定性、实现成本"},
        ],
    },
    {
        "title": "RAG+工作流",
        "points": [
            {"text": "内容的灵活性、工作流的复杂度、开发成本"},
        ],
    },
    {
        "title": "提示词",
        "points": [
            {"text": "稳定、调试和维护成本低"},
        ],
    },
]

by_id["Q13_31"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "老板提出"},
        ],
    },
    {
        "title": "理由",
        "points": [
            {"text": "新商业模式AI不适合介入、时间节点限制"},
        ],
    },
]

by_id["Q13_30"]["memoryKeywords"] = [
    {
        "title": "定位",
        "points": [
            {"text": "对问题进行识别、分流处理"},
        ],
    },
    {
        "title": "背景",
        "points": [
            {"text": "直播课堂存在影响上课连续性的设备问题"},
        ],
    },
    {
        "title": "AI处理",
        "points": [
            {"text": "对问题进行识别和分流"},
        ],
    },
    {
        "title": "AI不处理",
        "points": [
            {"text": "判断真实故障原因"},
        ],
    },
    {
        "title": "我做的四件事情",
        "points": [
            {"label": "1", "text": "场景、类型、方案"},
            {"label": "2", "text": "映射关系"},
            {"label": "3", "text": "技术方案验证"},
            {"label": "4", "text": "内部测试验收"},
        ],
    },
    {
        "title": "结果",
        "points": [
            {"text": "识别率92%"},
            {"text": "没有真实使用"},
        ],
    },
]

by_id["Q12_29"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "学前诊断策略、练习机制"},
        ],
    },
    {
        "title": "学前诊断策略",
        "points": [
            {"label": "当前的不足", "text": "缺少动态校准"},
            {"label": "优化方向", "text": "先初步诊断、再能力定位、最后确认"},
        ],
    },
    {
        "title": "练习机制",
        "points": [
            {"label": "当前的不足", "text": "题目自适应，仅解决下一步练什么"},
            {"label": "优化方向", "text": "教学自适应，解决发现问题"},
        ],
    },
    {
        "title": "没有立即优化的原因",
        "points": [
            {"label": "学前诊断策略", "text": "前面的策略已经落地实现"},
            {"label": "练习机制", "text": "当前基础能力和AI能力不支持"},
        ],
    },
]

by_id["Q21_44"]["memoryKeywords"] = [
    {
        "title": "结论｜基础原理",
        "points": [
            {
                "label": "Transformer",
                "text": "token化、向量化、自注意力机制-上下文关系，多层网络加工，基于当前context预测下一个token",
            },
            {
                "label": "Embedding",
                "text": "词向量模型，汉字向量化，语义关系以向量空间表达",
            },
        ],
    },
    {
        "title": "了解的背景",
        "points": [
            {"text": "在模型刚兴起时，建立基础认知，上层能力的实践"},
        ],
    },
    {
        "title": "现在的复盘",
        "points": [
            {
                "text": "理解做原生AI产品，为什么要重点关注当前轮应该给模型什么样的context",
            },
        ],
    },
]

by_id["Q17_59"]["memoryKeywords"] = ["懂说话", "能抗骂", "敢飙脏话"]

by_id["Q09_22"]["memoryKeywords"] = [
    {
        "title": "产品形态",
        "points": [
            {"text": "涵盖四大场景的诊学练评系统"},
        ],
    },
    {
        "title": "背景",
        "points": [
            {"text": "面向C端，独立运营和收费"},
        ],
    },
    {
        "title": "目标",
        "points": [
            {"text": "提供针对性的学练路径"},
        ],
    },
    {
        "title": "阻碍",
        "points": [
            {"text": "三大问题（判断学什么，练什么；持续使用；规模化执行）"},
        ],
    },
    {
        "title": "行动",
        "points": [
            {"label": "1", "text": "竞品调研，确定机制"},
            {"label": "2", "text": "数据、激励机制实现差异化"},
            {"label": "3", "text": "配置后台实现规模化"},
        ],
    },
]

by_id["Q09_23"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "不是由某一个人一开始提出来的，是我复盘的时候抽象的"},
        ],
    },
    {
        "title": "第一问",
        "points": [
            {"text": "源于公司战略目标"},
        ],
    },
    {
        "title": "第二问",
        "points": [
            {"text": "源于产品总监从销售的角度提出"},
        ],
    },
    {
        "title": "第三问",
        "points": [
            {"text": "源于公司历史业务痛点"},
        ],
    },
]

by_id["Q09_25"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "思维方式的转变"},
        ],
    },
    {
        "title": "过去",
        "points": [
            {"text": "标书项目、优化项目"},
        ],
    },
    {
        "title": "本次",
        "points": [
            {"text": "没有业务需求、没有售卖出去"},
        ],
    },
    {
        "title": "业务需求",
        "points": [
            {"text": "差异化设计的思考"},
        ],
    },
    {
        "title": "售卖出去",
        "points": [
            {"text": "商业模式推演"},
        ],
    },
]

by_id["Q09_26"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "按需调研"},
        ],
    },
    {
        "title": "成形产品",
        "points": [
            {"text": "了解本质问题，根据实际需要通过市场部资源，或到校体验竞品进行调研"},
        ],
    },
    {
        "title": "从0-1的产品",
        "points": [
            {"text": "基于需求目标，线上收集资料，线下友商体验"},
        ],
    },
]

by_id["Q10_27"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "总监提出，我拆解指标"},
        ],
    },
    {
        "title": "拆解思路",
        "points": [
            {"text": "通过行为，确定数据"},
            {"text": "通过数据，判断激励导向"},
            {"text": "通过激励行为，确定资源学习数量统计、正确率、新增掌握度数量等"},
        ],
    },
]

by_id["Q11_28"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "分业务模式拆解成本和收益"},
        ],
    },
    {
        "title": "成本",
        "points": [
            {"text": "硬件成本和AI算力成本（输入输出的token均值、一学年的使用频次、折算人均年度成本）"},
        ],
    },
    {
        "title": "收入",
        "points": [
            {"text": "单校用户规模、付费转化率、ARPPU等变量"},
        ],
    },
    {
        "title": "收获",
        "points": [
            {"text": "对于商业收益这块的计算有了基础的了解"},
        ],
    },
]

by_id["Q06_15"]["memoryKeywords"] = [
    {
        "title": "用户价值",
        "points": [
            {"text": "真、强、难"},
        ],
    },
    {
        "title": "业务价值",
        "points": [
            {"text": "增量收益"},
        ],
    },
    {
        "title": "技术实现",
        "points": [
            {"text": "闭环、可控"},
        ],
    },
]

by_id["Q06_17"]["memoryKeywords"] = ["涉及轻量的Tool Use"]

by_id["Q06_19"]["memoryKeywords"] = ["回答实现能力的机制里去逐层判断"]

by_id["Q07_13"]["memoryKeywords"] = ["方案构思阶段", "方案落地阶段", "Harness阶段"]

by_id["Q08_14"]["memoryKeywords"] = ["输入识别", "意图识别", "上下文管理", "安全边界限制"]

by_id["Q01_1"]["memoryKeywords"] = [
    {
        "title": "场景",
        "points": [
            {"text": "需求洞察"},
        ],
    },
    {
        "title": "模型",
        "points": [
            {"text": "稳定性、兜底方式"},
        ],
    },
]

by_id["Q02_2"]["memoryKeywords"] = [
    {
        "title": "结论",
        "points": [
            {"text": "具体业务链路里，模型不稳定性带来的风险是不是可接受、可发现、可兜底的。"},
        ],
    },
    {
        "title": "核心三要素",
        "points": [
            {"text": "准确率和稳定性、错误成本、兜底措施"},
        ],
    },
    {
        "title": "举例",
        "points": [
            {"text": "AI答疑项目、ocr项目"},
        ],
    },
    {
        "title": "总结",
        "points": [
            {"text": "直接使用的，需谨慎；可纠正的，重产品机制"},
        ],
    },
]

by_id["Q04_4"]["memoryKeywords"] = [
    {
        "title": "招投标项目",
        "points": [
            {"text": "主要流程、关键环节（PRD、demo演示）"},
        ],
    },
    {
        "title": "战略规划项目",
        "points": [
            {"text": "主要流程"},
        ],
    },
]

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
jp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(root / "data" / "questions.js").write_text(
    f"window.QUESTION_DATA = {payload};\n", encoding="utf-8"
)
print("updated keywords incl. Q09_22")
