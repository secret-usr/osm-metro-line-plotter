METRO_LINES = [
    # 关系：1号线：萧山机场 -> 湘湖 (4627561)
    {
        'name': 'line 1',
        'relation_id': 4627561,
    },
    # 关系：2号线：朝阳 -> 良渚 (5454457)
    {
        'name': 'line 2',
        'relation_id': 5454457,
    },
    # 关系：3号线：吴山前村 -> 星桥 (13538220)
    {
        'name': 'line 3a',
        'relation_id': 13538220,
    },
    # 关系：3号线：石马 -> 星桥 (14280625)
    {
        'name': 'line 3b',
        'relation_id': 14280625,
    },
    # 关系：4号线：浦沿 -> 池华街 (9641050)
    {
        'name': 'line 4',
        'relation_id': 9641050,
    },
    # 关系：5号线：姑娘桥 -> 南湖东 (10386965)
    {
        'name': 'line 5',
        'relation_id': 10386965,
    },
    # 关系：6号线：桂花西路 -> 枸桔弄 (13077286)
    {
        'name': 'line 6a',
        'relation_id': 13077286,
    },
    # 关系：6号线：双浦 -> 枸桔弄 (13077349)
    {
        'name': 'line 6b',
        'relation_id': 13077349,
    },
    # 关系：7号线：吴山广场 -> 江东二路 (13061278)
    {
        'name': 'line 7',
        'relation_id': 13061278,
    },
    # 关系：8号线：文海南路 -> 新湾路 (13042426)
    {
        'name': 'line 8',
        'relation_id': 13042426,
    },
    # 关系：9号线：观音塘 -> 龙安 (13060896)
    {
        'name': 'line 9',
        'relation_id': 13060896,
    },
    # 关系：10号线：黄龙体育中心 -> 逸盛路 (13535687)
    {
        'name': 'line 10',
        'relation_id': 13535687,
    },
    # 关系：16号线：绿汀路 -> 九州街 (11076297)
    {
        'name': 'line 16',
        'relation_id': 11076297,
    },
    # 关系：19号线：火车西站 -> 永盛路 (14613131)
    {
        'name': 'line 19',
        'relation_id': 14613131,
    },
    # 关系：杭海城际铁路：临平南高铁站 -> 浙大国际校区 (13078549)
    {
        'name': 'hanghai intercity',
        'relation_id': 13078549,
    },
    # 关系：绍兴 1号线：姑娘桥 -> 芳泉 (12920989)
    {
        'name': 'shaoxing line 1a',
        'relation_id': 12920989,
    },
    # 关系：绍兴 1号线：大庆寺 -> 芳泉 (17438392)
    {
        'name': 'shaoxing line 1b',
        'relation_id': 17438392,
    }
]

# 反向映射
LINE_NAME_TO_INDEX = {line['name']: i for i, line in enumerate(METRO_LINES)}
LINE_NAME_TO_RELATION_ID = {line['name']: line['relation_id'] for line in METRO_LINES}