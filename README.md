地下铁实际走向绘制器

| 杭州地铁 2025| 区间：古荡-浙大国际校区|
|:-:|:-:|
| ![fig1](./figure/Figure_1.png) | ![fig2](./figure/Figure_2.png) |

从 OpenStreetMap 请求数据，绘制指定的线路或区间的实际走向。

## 依赖

```python
pip install requests matplotlib numpy
```

## 说明

1. 需要手动在 OpenStreetMap 中找到线路对应的关系 id ，例如[杭州地铁三号线从吴山前村往星桥方向](https://www.OpenStreetMap.org/relation/13538220)，对应的关系 id 为 13538220。

2. 可以在 `config.py` 中的 `METRO_LINES` 列表添加线路的配置，以便后续批量绘制。

3. `plotter.process_metro_line(relation_id)` 

该方法从 OpenStreetMap 获取数据并处理，然后生成一个 json 文件，文件名为 `metro_line_id.json`，例如 `metro_line_13538220.json`。

返回值为文件名。

如果当前目录下已经存在对应的 json 文件，则会检查其内容是否合法，如果合法则直接返回文件名；如果不合法或不存在，则会重新获取数据并生成新的 json 文件。

4. `plotter.plot_multiple_lines(json_filenames, fig=None, ax=None, alpha=0.8, show_plot=True)` 

该方法绘制多个线路的实际走向图，传入的必选参数 `json_filenames` 为一个列表，列表中的每个元素都是一个 json 文件的路径，例如 `['metro_line_13538220.json']`。可选参数 `fig` 和 `ax` 指定 matplotlib 的图形和坐标轴对象，如果不传入则会自动创建新的图形和坐标轴；可选参数 `alpha` 控制线路的不透明度；可选参数 `show_plot` 控制是否显示绘图结果。

返回值为 matplotlib 的图形和坐标轴对象 `fig` 和 `ax`。

5. `plot_multiple_segments(segment_configs, fig=None, ax=None, alpha=0.8, show_plot=True)` 

该方法绘制多个指定区间的实际走向图，传入的必选参数 `segment_configs` 为一个列表，列表中的每个元素都是一个包含起点和终点的字典，例如 `[{json_filename: 'metro_line_13538220.json', start_station: '西湖文化广场', end_station: '古荡'}]`。可选参数 `fig` 和 `ax` 指定 matplotlib 的图形和坐标轴对象，如果不传入则会自动创建新的图形和坐标轴；可选参数 `alpha` 控制线路的不透明度；可选参数 `show_plot` 控制是否显示绘图结果。

返回值为 matplotlib 的图形和坐标轴对象 `fig` 和 `ax`。

6. 使用示例

```python
# file: config.py
METRO_LINES = [
    # ...
    {
        'name': 'line 3a',
        'relation_id': 13538220,
    },
    # ...
]

# 反向映射
LINE_NAME_TO_INDEX = {line['name']: i for i, line in enumerate(METRO_LINES)}
LINE_NAME_TO_RELATION_ID = {line['name']: line['relation_id'] for line in METRO_LINES}
```

```python
# file: main.py
if __name__ == "__main__":
    plotter = MetroLinePlotter()
    
    # 处理所有线路
    json_filenames = []
    for line in METRO_LINES:
            filename = plotter.process_metro_line(relation_id=line['relation_id'])
            if filename:
                json_filenames.append(filename)

    # 如果需要强制更新某条线路的缓存
    # json_filenames.append(plotter.process_metro_line(relation_id=13538220, force_update=True))

    # 绘制完整线路图
    if json_filenames:
        fig, ax = plotter.plot_multiple_lines(json_filenames, alpha=0.1, show_plot=False)
    
    # 再上图基础上绘制多个区间
    if json_filenames:
        segment_configs = [
            {
                'json_filename': json_filenames[LINE_NAME_TO_INDEX["line 3a"]],
                'start_station': '古荡',
                'end_station': '西湖文化广场'
            },
            {
                'json_filename': json_filenames[LINE_NAME_TO_INDEX["line 1"]],
                'start_station': '西湖文化广场',
                'end_station': '客运中心'
            },
            {
                'json_filename': json_filenames[LINE_NAME_TO_INDEX["line 9"]],
                'start_station': '客运中心',
                'end_station': '余杭高铁站'
            },
            {
                'json_filename': json_filenames[LINE_NAME_TO_INDEX["hanghai intercity"]],
                'start_station': '临平南高铁站',
                'end_station': '浙大国际校区'
            }
        ]
        # 最后一个绘图的函数需要传入 show_plot=True
        plotter.plot_multiple_segments(segment_configs, fig, ax, show_plot=True)
```

## 声明

1. 关于数据准确性

OpenStreetMap 数据可能与现实存在时间滞后或地理偏差，仅供参考，实际情况请以官方或实地资料为准。

2. 关于代码生成与使用

本项目中的 Python 代码几乎全部由人工智能辅助生成，作者对其中的功能逻辑进行了调试和必要修改。由于自动生成代码的局限性，部分实现可能存在错误或不完善之处，欢迎使用者在实际应用中根据需要进一步优化与修改。