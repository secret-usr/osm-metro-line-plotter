地下铁实际走向绘制器

从 openstreetmap 请求数据，绘制指定的线路或区间的实际走向。

首先在 openstreetmap 中找到线路对应的关系 id ，例如[杭州地铁三号线从吴山前村往星桥方向](https://www.openstreetmap.org/relation/13538220)，对应的关系 id 为 13538220。

然后通过 `plotter.process_metro_line(relation_id=13538220)` 方法生成线路的走向信息，这将会从 openstreetmap 获取数据并处理，然后生成一个 json 文件，文件名为 `metro_line_id.json`，例如 `metro_line_13538220.json`。

接下来可以通过 `plotter.plot_multiple_lines()` 方法绘制线路的实际走向图，传入的参数为一个列表，列表中的每个元素都是一个 json 文件的路径，例如 `['metro_line_13538220.json']`；也可以通过 `plotter.plot_from_json('metro_line_13538220.json')` 方法直接绘制单个指定的 json 文件。

如果需要绘制某个区间而非完整线路，通过 `plotter.plot_multiple_segments()` 方法进行绘制，传入的参数为一个列表，列表中的每个元素都是一个包含起点和终点的字典，例如 `[{json_filename: 'metro_line_13538220.json', start_station: '西湖文化广场', end_station: '古荡'}]`；也可以通过 `plotter.plot_segment_from_json('metro_line_13538220.json', start_station='西湖文化广场', end_station='古荡')` 方法直接绘制单个指定的区间。

使用示例：

```python
```

AIGC 申明：全部的 python 代码均由人工智能工具生成，本人仅负责调试和修改部分细节，代码中可能存在错误或不完善的地方，请自行调试和修改。