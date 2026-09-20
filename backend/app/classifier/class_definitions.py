"""Versioned class definitions shared by runtime and local training."""

V2_CLASS_DEFINITIONS = [
    {"short": "AD", "name": "特应性皮炎", "risk_level": "routine", "description": "常见慢性炎症性皮肤问题，可表现为干燥、发红和瘙痒，需要结合病史判断。"},
    {"short": "BCC", "name": "基底细胞癌", "risk_level": "urgent", "description": "模型发现与基底细胞癌训练样本相似的特征，建议尽快由皮肤科医生面诊确认。"},
    {"short": "ECZEMA", "name": "湿疹", "risk_level": "routine", "description": "常见炎症性皮肤表现，可能与刺激、过敏或皮肤屏障受损有关。"},
    {"short": "MEL", "name": "黑色素瘤", "risk_level": "urgent", "description": "模型发现与黑色素瘤训练样本相似的特征，请尽快到皮肤科进行专业评估。"},
    {"short": "WARTS", "name": "疣或传染性软疣", "risk_level": "routine", "description": "可能与疣或传染性软疣的外观相似，部分具有传染性，应避免抓挠和共用毛巾。"},
]

V3_CLASS_DEFINITIONS = [
    {"short": "ACNE", "name": "痤疮或酒渣鼻", "risk_level": "routine", "description": "可表现为粉刺、丘疹、脓疱或面部持续潮红，需要结合年龄、部位和诱因判断。"},
    {"short": "AK", "name": "光化性角化", "risk_level": "urgent", "description": "日晒部位反复出现粗糙、脱屑或结痂时，建议尽快由皮肤科评估。"},
    *V2_CLASS_DEFINITIONS[:1],
    {"short": "BACT", "name": "常见细菌性皮肤感染", "risk_level": "routine", "description": "可能与脓疱疮、蜂窝织炎等细菌感染外观相似；红肿迅速扩大或伴发热时应及时就医。"},
    *V2_CLASS_DEFINITIONS[1:2],
    {"short": "CONTACT", "name": "接触性皮炎", "risk_level": "routine", "description": "可能与清洁剂、金属、植物、护肤品或其他刺激物和过敏原接触有关。"},
    *V2_CLASS_DEFINITIONS[2:3],
    {"short": "FUNGAL", "name": "常见真菌性皮肤感染", "risk_level": "routine", "description": "癣、念珠菌等真菌感染可呈环形红斑、边缘脱屑或潮湿糜烂，需要检查确认。"},
    {"short": "HERPES", "name": "疱疹及相关病毒性皮损", "risk_level": "routine", "description": "成簇水疱、疼痛或沿神经分布的皮损可能与疱疹相关，眼周或伴明显全身症状时应尽快就医。"},
    *V2_CLASS_DEFINITIONS[3:4],
    {"short": "PSO", "name": "银屑病或扁平苔藓样皮损", "risk_level": "routine", "description": "可表现为边界较清楚的红斑、鳞屑或紫红色丘疹，需要皮肤科结合病史鉴别。"},
    {"short": "SEK", "name": "脂溢性角化或其他良性肿物", "risk_level": "routine", "description": "常见良性隆起或贴附样病变，但新发、快速变化或出血时仍需面诊排除恶性病变。"},
    {"short": "SCC", "name": "鳞状细胞癌", "risk_level": "urgent", "description": "持续增大、破溃、出血或反复结痂的可疑病变应尽快由皮肤科评估。"},
    {"short": "URT", "name": "荨麻疹", "risk_level": "routine", "description": "可表现为短时间出现和消退的风团；伴呼吸困难、喉头紧缩时应立即就医。"},
    *V2_CLASS_DEFINITIONS[4:5],
]

CLASS_PROFILES = {"v2": V2_CLASS_DEFINITIONS, "v3": V3_CLASS_DEFINITIONS}
