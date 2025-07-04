import requests
import json
import matplotlib.pyplot as plt
import numpy as np
import math
import os
from config import METRO_LINES, LINE_NAME_TO_INDEX, LINE_NAME_TO_RELATION_ID

class MetroLinePlotter:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def get_metro_line_data(self, relation_id):
        """获取地铁线路数据"""
        query = f"""
        [out:json][timeout:25];
        (
          relation({relation_id});
        );
        (._;>;);
        out geom;
        """
        
        try:
            print(f"正在请求关系 {relation_id} 的数据...")
            response = requests.post(self.overpass_url, data=query)
            response.raise_for_status()
            data = response.json()
            print(f"成功获取数据，包含 {len(data.get('elements', []))} 个元素")
            return data
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    def merge_ways(self, ways_info):
        """合并所有way为一条连续路径"""
        if not ways_info:
            return []
        
        print(f"开始合并 {len(ways_info)} 个way...")
        
        # 创建way坐标副本
        remaining_ways = []
        for way in ways_info:
            remaining_ways.append({
                'id': way['id'],
                'coordinates': way['coordinates'].copy(),
                'used': False
            })
        
        # 选择第一个way作为起点
        merged_coords = remaining_ways[0]['coordinates'].copy()
        remaining_ways[0]['used'] = True
        print(f"起始way {remaining_ways[0]['id']} 包含 {len(merged_coords)} 个点")
        
        # 逐个连接其他way
        while True:
            found_connection = False
            
            for way in remaining_ways:
                if way['used']:
                    continue
                
                # 检查与当前合并路径的连接
                current_start = merged_coords[0]
                current_end = merged_coords[-1]
                way_start = way['coordinates'][0]
                way_end = way['coordinates'][-1]
                
                # 计算各种连接可能性
                connections = [
                    ('end_to_start', self.calculate_distance(current_end[1], current_end[0], way_start[1], way_start[0])),
                    ('end_to_end', self.calculate_distance(current_end[1], current_end[0], way_end[1], way_end[0])),
                    ('start_to_start', self.calculate_distance(current_start[1], current_start[0], way_start[1], way_start[0])),
                    ('start_to_end', self.calculate_distance(current_start[1], current_start[0], way_end[1], way_end[0]))
                ]
                
                # 找到最近的连接
                best_connection = min(connections, key=lambda x: x[1])
                
                if best_connection[1] < 100:  # 100米内认为是连接的
                    connection_type = best_connection[0]
                    
                    if connection_type == 'end_to_start':
                        # 在末尾添加way（去掉重复点）
                        merged_coords.extend(way['coordinates'][1:])
                    elif connection_type == 'end_to_end':
                        # 在末尾添加反向way（去掉重复点）
                        merged_coords.extend(way['coordinates'][-2::-1])
                    elif connection_type == 'start_to_start':
                        # 在开头添加反向way（去掉重复点）
                        merged_coords = way['coordinates'][-1:0:-1] + merged_coords
                    elif connection_type == 'start_to_end':
                        # 在开头添加way（去掉重复点）
                        merged_coords = way['coordinates'][:-1] + merged_coords
                    
                    way['used'] = True
                    found_connection = True
                    print(f"连接way {way['id']} ({connection_type}), 距离: {best_connection[1]:.1f}m")
                    break
            
            if not found_connection:
                break
        
        # 检查未使用的way
        unused_ways = [way for way in remaining_ways if not way['used']]
        if unused_ways:
            print(f"警告: {len(unused_ways)} 个way未能连接:")
            for way in unused_ways:
                print(f"  - way {way['id']}")
        
        print(f"合并完成，总共 {len(merged_coords)} 个坐标点")
        return merged_coords

    def insert_stations_into_path(self, merged_coords, stations):
        """将车站信息插入到合并后的路径中"""
        if not merged_coords or not stations:
            return []
        
        print(f"开始将 {len(stations)} 个车站插入路径...")
        
        # 创建路径点列表
        path_points = []
        for coord in merged_coords:
            path_points.append({
                'lat': coord[1],
                'lon': coord[0],
                'is_station': False,
                'station_name': None
            })
        
        # 为每个车站找到最近的路径点
        for station in stations:
            min_distance = float('inf')
            best_index = 0
            
            # 找到距离车站最近的路径点
            for i, point in enumerate(path_points):
                distance = self.calculate_distance(
                    station['lat'], station['lon'],
                    point['lat'], point['lon']
                )
                if distance < min_distance:
                    min_distance = distance
                    best_index = i
            
            print(f"车站 {station['name']} 最近点距离: {min_distance:.1f}m")
            
            if min_distance < 500:  # 500米内认为是有效的车站位置
                # 检查是否应该插入新点还是更新现有点
                if min_distance < 50:  # 50米内直接更新现有点
                    path_points[best_index]['is_station'] = True
                    path_points[best_index]['station_name'] = station['name']
                    print(f"  -> 更新现有点为车站")
                else:
                    # 插入新的车站点
                    # 判断插入位置（前面还是后面）
                    if best_index == 0:
                        insert_index = 0
                    elif best_index == len(path_points) - 1:
                        insert_index = len(path_points)
                    else:
                        # 计算到前一个点和后一个点的距离，选择更合适的插入位置
                        prev_distance = self.calculate_distance(
                            station['lat'], station['lon'],
                            path_points[best_index-1]['lat'], path_points[best_index-1]['lon']
                        )
                        next_distance = self.calculate_distance(
                            station['lat'], station['lon'],
                            path_points[best_index+1]['lat'], path_points[best_index+1]['lon']
                        )
                        
                        if prev_distance < next_distance:
                            insert_index = best_index
                        else:
                            insert_index = best_index + 1
                    
                    station_point = {
                        'lat': station['lat'],
                        'lon': station['lon'],
                        'is_station': True,
                        'station_name': station['name']
                    }
                    path_points.insert(insert_index, station_point)
                    print(f"  -> 在索引 {insert_index} 插入新车站点")
            else:
                print(f"  -> 车站距离过远，跳过")
        
        print(f"路径处理完成，总共 {len(path_points)} 个点")
        return path_points

    def extract_line_info(self, data):
        """提取线路基本信息（名称、颜色等）"""
        relation_info = {'name': '未知线路', 'colour': '#000000'}
        
        for element in data.get('elements', []):
            if element['type'] == 'relation' and 'tags' in element:
                tags = element['tags']
                # 提取线路名称
                relation_info['name'] = tags.get('name', 
                                               tags.get('name:zh', 
                                                       tags.get('name:en', '未知线路')))
                # 提取线路颜色
                relation_info['colour'] = tags.get('colour', '#000000')
                print(f"线路信息: {relation_info['name']}, 颜色: {relation_info['colour']}")
                break
        
        return relation_info

    def extract_line_geometry(self, data):
        """从JSON数据中提取几何信息"""
        stations = []
        ways_info = []
        
        elements = data.get('elements', [])
        print(f"调试信息: 元素数量: {len(elements)}")
        
        # 提取车站节点
        for element in elements:
            if element['type'] == 'node' and 'tags' in element:
                tags = element['tags']
                if (tags.get('railway') == 'stop' or 
                    tags.get('railway') == 'station'):
                    
                    station_name = tags.get('name', 
                                          tags.get('name:zh', 
                                                  tags.get('name:en', f'站点{element["id"]}')))
                    stations.append({
                        'name': station_name,
                        'lat': float(element['lat']),
                        'lon': float(element['lon']),
                        'id': element['id']
                    })
                    print(f"找到车站: {station_name}")
        
        # 提取每个way的坐标信息
        for element in elements:
            if element['type'] == 'way' and 'geometry' in element:
                way_coords = []
                for point in element['geometry']:
                    coord = [float(point['lon']), float(point['lat'])]
                    way_coords.append(coord)
                
                # 保存way信息
                way_info = {
                    'id': element['id'],
                    'coordinates': way_coords.copy()
                }
                ways_info.append(way_info)
                print(f"从way {element['id']} 添加了 {len(way_coords)} 个坐标点")
        
        print(f"最终提取到 {len(stations)} 个车站, {len(ways_info)} 个ways")
        return stations, ways_info

    def save_to_json(self, path_points, relation_id, relation_info, filename=None):
        """保存路径数据到JSON文件"""
        if filename is None:
            filename = f"metro_line_{relation_id}.json"
        
        output_data = {
            'relation_id': relation_id,
            'name': relation_info['name'],
            'colour': relation_info['colour'],
            'total_points': len(path_points),
            'station_count': len([p for p in path_points if p['is_station']]),
            'path_points': path_points
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {filename}")
            print(f"线路: {output_data['name']}")
            print(f"颜色: {output_data['colour']}")
            print(f"总点数: {output_data['total_points']}")
            print(f"车站数: {output_data['station_count']}")
            return filename
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None

    def process_metro_line(self, relation_id, force_update=False):
        """处理地铁线路数据并生成JSON
        
        Args:
            relation_id: OSM关系ID
            force_update: 是否强制更新，默认False
        """
        # 生成文件名
        filename = f"metro_line_{relation_id}.json"
        # 如果文件已存在且不强制更新，直接返回现有文件
        if os.path.exists(filename) and not force_update:
            print(f"文件 {filename} 已存在，直接使用现有文件")
            # 验证文件是否有效
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('path_points'):
                    print(f"验证通过: {data.get('name', '未知线路')}")
                    print(f"总点数: {data.get('total_points', 0)}")
                    print(f"车站数: {data.get('station_count', 0)}")
                    return filename
                else:
                    print(f"文件 {filename} 格式无效，将重新生成")
            except Exception as e:
                print(f"文件 {filename} 读取失败: {e}，将重新生成")

            # 如果文件不存在或无效，重新获取数据
        print(f"正在处理关系 {relation_id} 的数据...")
        data = self.get_metro_line_data(relation_id)
        
        if not data:
            print("无法获取数据")
            return None
        
        # 提取线路基本信息
        relation_info = self.extract_line_info(data)
        
        # 提取几何信息
        stations, ways_info = self.extract_line_geometry(data)
        
        if not ways_info:
            print("未找到线路坐标数据")
            return None
        
        # 步骤1: 合并所有way为一条连续路径
        merged_coords = self.merge_ways(ways_info)
        
        if not merged_coords:
            print("无法合并way数据")
            return None
        
        # 步骤2: 将车站信息插入路径
        path_points = self.insert_stations_into_path(merged_coords, stations)
        
        # 步骤3: 保存到JSON文件
        filename = self.save_to_json(path_points, relation_id, relation_info, filename)
        
        return filename

    def plot_from_json(self, json_filename, fig=None, ax=None, alpha = 0.8, show_plot=True):
        """从JSON文件读取数据并绘制地铁线路图"""
        try:
            with open(json_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return None, None
        
        path_points = data.get('path_points', [])
        line_name = data.get('name', '地铁线路')
        line_color = data.get('colour', '#000000')
        
        if not path_points:
            print("JSON文件中没有路径数据")
            return None, None
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 如果没有提供fig和ax，创建新的
        if fig is None or ax is None:
            fig, ax = plt.subplots(1, 1, figsize=(16, 10))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            # 设置图形属性（仅在创建新图时设置）
            ax.set_aspect('equal', adjustable='box')
            # 移除网格、坐标轴标签和刻度
            ax.grid(False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel('')
            ax.set_ylabel('')
            # 移除坐标轴边框
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
        
        # 分离线路点和车站点
        line_points = []
        stations = []
        
        for point in path_points:
            line_points.append([point['lon'], point['lat']])
            if point['is_station']:
                stations.append({
                    'name': point['station_name'],
                    'lon': point['lon'],
                    'lat': point['lat']
                })
        
        # 绘制线路（移除label参数）
        if line_points:
            coords_array = np.array(line_points)
            ax.plot(coords_array[:, 0], coords_array[:, 1], 
                color=line_color, linewidth=4, solid_capstyle='round',
                alpha=alpha, zorder=1)
        
        # 绘制车站
        for station in stations:
            ax.plot(station['lon'], station['lat'], 'o', 
                color='white', markersize=3, markeredgecolor=line_color, 
                markeredgewidth=0, zorder=1)
            
            # 添加车站名称标签
            # ax.annotate(station['name'], 
            #         (station['lon'], station['lat']),
            #         xytext=(0, -10), textcoords='offset points',
            #         fontsize=8, ha='center', va='center')
        
        # 更新坐标轴范围以包含新线路
        all_lons = [p[0] for p in line_points]
        all_lats = [p[1] for p in line_points]
        
        if all_lons and all_lats:
            # 获取当前坐标轴范围
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
            
            # 计算新的范围
            new_min_lon = min(min(all_lons), current_xlim[0])
            new_max_lon = max(max(all_lons), current_xlim[1])
            new_min_lat = min(min(all_lats), current_ylim[0])
            new_max_lat = max(max(all_lats), current_ylim[1])
            
            # 添加边距
            lon_margin = (new_max_lon - new_min_lon) * 0.05
            lat_margin = (new_max_lat - new_min_lat) * 0.05
            
            ax.set_xlim(new_min_lon - lon_margin, new_max_lon + lon_margin)
            ax.set_ylim(new_min_lat - lat_margin, new_max_lat + lat_margin)
        
        # 只有在show_plot为True时才显示图形
        if show_plot:
            plt.tight_layout()
            plt.show()
        
        print(f"绘制完成: {line_name}")
        print(f"总点数: {len(path_points)}")
        print(f"车站数: {len(stations)}")
        
        return fig, ax
        
    def plot_multiple_lines(self, json_filenames, fig=None, ax=None, alpha=0.8, show_plot=True):
        """一次性绘制多条线路
        Args:
            json_filenames: 线路信息 json 文件名列表
            alpha: 不透明度
            show_plot: 是否显示图形
        """
        if not json_filenames:
            print("没有提供JSON文件")
            return fig, ax
        
        for i, filename in enumerate(json_filenames):
            # 最后一条线路时显示图形
            show = show_plot and (i == len(json_filenames) - 1)
            fig, ax = self.plot_from_json(filename, fig, ax, alpha=alpha, show_plot=show)
            
            if fig is None or ax is None:
                print(f"绘制 {filename} 失败")
                continue
        
        return fig, ax

    def find_station_index(self, path_points, station_name):
        """在路径中查找车站的索引位置"""
        for i, point in enumerate(path_points):
            if point['is_station'] and point['station_name'] == station_name:
                return i
        return -1

    def extract_segment(self, path_points, start_station, end_station):
        """提取两个车站之间的路径段"""
        start_index = self.find_station_index(path_points, start_station)
        end_index = self.find_station_index(path_points, end_station)
        
        if start_index == -1:
            print(f"未找到起始车站: {start_station}")
            return []
        
        if end_index == -1:
            print(f"未找到终点车站: {end_station}")
            return []
        
        # 确保start_index小于end_index
        if start_index > end_index:
            start_index, end_index = end_index, start_index
            print(f"已调整顺序: {end_station} -> {start_station}")
        
        # 提取区间内的所有点
        segment_points = path_points[start_index:end_index + 1]
        
        print(f"提取区间: {start_station} -> {end_station}")
        print(f"区间包含 {len(segment_points)} 个点")
        
        return segment_points

    def plot_segment_from_json(self, json_filename, start_station, end_station, fig=None, ax=None, alpha=0.8, show_plot=True):
        """从JSON文件读取数据并绘制指定区间的地铁线路图"""
        try:
            with open(json_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return None, None
        
        path_points = data.get('path_points', [])
        line_name = data.get('name', '地铁线路')
        line_color = data.get('colour', '#000000')
        
        if not path_points:
            print("JSON文件中没有路径数据")
            return None, None
        
        # 提取指定区间的路径段
        segment_points = self.extract_segment(path_points, start_station, end_station)
        
        if not segment_points:
            print("无法提取指定区间")
            return None, None
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 如果没有提供fig和ax，创建新的
        if fig is None or ax is None:
            fig, ax = plt.subplots(1, 1, figsize=(16, 10))
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            # 设置图形属性（仅在创建新图时设置）
            ax.set_aspect('equal', adjustable='box')
            # 移除网格、坐标轴标签和刻度
            ax.grid(False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel('')
            ax.set_ylabel('')
            # 移除坐标轴边框
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
        
        # 分离线路点和车站点
        line_points = []
        stations = []
        
        for point in segment_points:
            line_points.append([point['lon'], point['lat']])
            if point['is_station']:
                stations.append({
                    'name': point['station_name'],
                    'lon': point['lon'],
                    'lat': point['lat']
                })
        
        # 绘制线路
        if line_points:
            coords_array = np.array(line_points)
            ax.plot(coords_array[:, 0], coords_array[:, 1], 
                color=line_color, linewidth=4, solid_capstyle='round',
                alpha=alpha, zorder=1)
        
        # 绘制车站
        for station in stations:
            ax.plot(station['lon'], station['lat'], 'o', 
                color='white', markersize=3, markeredgecolor=line_color, 
                markeredgewidth=0, zorder=1)
            
            # 添加车站名称标签
            # ax.annotate(station['name'], 
            #         (station['lon'], station['lat']),
            #         xytext=(0, -10), textcoords='offset points',
            #         fontsize=8, ha='center', va='center')
        
        # 更新坐标轴范围以包含新线路（与 plot_from_json 保持一致）
        all_lons = [p[0] for p in line_points]
        all_lats = [p[1] for p in line_points]
        
        if all_lons and all_lats:
            # 获取当前坐标轴范围
            current_xlim = ax.get_xlim()
            current_ylim = ax.get_ylim()
            
            # 计算新的范围
            new_min_lon = min(min(all_lons), current_xlim[0])
            new_max_lon = max(max(all_lons), current_xlim[1])
            new_min_lat = min(min(all_lats), current_ylim[0])
            new_max_lat = max(max(all_lats), current_ylim[1])
            
            # 添加边距
            lon_margin = (new_max_lon - new_min_lon) * 0.05
            lat_margin = (new_max_lat - new_min_lat) * 0.05
            
            ax.set_xlim(new_min_lon - lon_margin, new_max_lon + lon_margin)
            ax.set_ylim(new_min_lat - lat_margin, new_max_lat + lat_margin)
        
        # 只有在show_plot为True时才显示图形
        if show_plot:
            plt.tight_layout()
            plt.show()
        
        print(f"绘制完成: {line_name} ({start_station} -> {end_station})")
        print(f"区间点数: {len(segment_points)}")
        print(f"区间车站数: {len(stations)}")
        
        return fig, ax

    def plot_multiple_segments(self, segment_configs, fig=None, ax=None, alpha=0.8, show_plot=True):
        """绘制多个线路区间
        
        Args:
            segment_configs: 配置列表，每个配置包含:
                {
                    'json_filename': 'metro_line_xxx.json',
                    'start_station': '起始站名',
                    'end_station': '终点站名'
                }
            alpha: 不透明度
            show_plot: 是否显示图形
        """
        if not segment_configs:
            print("没有提供区间配置")
            return fig, ax
        
        for i, config in enumerate(segment_configs):
            json_filename = config.get('json_filename')
            start_station = config.get('start_station')
            end_station = config.get('end_station')
            
            if not all([json_filename, start_station, end_station]):
                print(f"配置 {i} 缺少必要参数")
                continue
            
            # 最后一个区间时显示图形
            show = show_plot and (i == len(segment_configs) - 1)
            fig, ax = self.plot_segment_from_json(
                json_filename, start_station, end_station,
                fig, ax, alpha=alpha, show_plot=show
            )
            
            if fig is None or ax is None:
                print(f"绘制区间 {start_station} -> {end_station} 失败")
                continue
        
        return fig, ax

# 使用示例
if __name__ == "__main__":
    plotter = MetroLinePlotter()
    
    # 处理线路
    json_filenames = []
    for line in METRO_LINES:
            filename = plotter.process_metro_line(relation_id=line['relation_id'])
            if filename:
                json_filenames.append(filename)

    # 如果需要强制更新某条线路的缓存
    # json_filenames.append(plotter.process_metro_line(relation_id=13538220, force_update=True))

    # 方法1: 绘制单条线路
    # if json_filenames:
    #     fig, ax = plotter.plot_from_json(json_filenames[LINE_NAME_TO_INDEX["line 3a"]], alpha = 0.8, show_plot=True)

    # 方法2: 绘制多条线路
    if json_filenames:
        fig, ax = plotter.plot_multiple_lines(json_filenames, alpha = 0.1, show_plot=False)
    
    # 方法3: 绘制单个区间
    # if json_filenames:
    #     plotter.plot_segment_from_json(
    #         json_filenames[LINE_NAME_TO_INDEX["line 3a"]], 
    #         start_station='西湖文化广场', 
    #         end_station='古荡',
    #         fig=fig, ax=ax, alpha=0.8, show_plot=True
    #     )
    
    # 方法4: 绘制多个区间
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
        plotter.plot_multiple_segments(segment_configs, fig, ax, show_plot=True)