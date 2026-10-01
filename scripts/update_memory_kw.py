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

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
jp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(root / "data" / "questions.js").write_text(
    f"window.QUESTION_DATA = {payload};\n", encoding="utf-8"
)
print("updated keywords incl. Q19_42, Q20_43, Q21_44")
