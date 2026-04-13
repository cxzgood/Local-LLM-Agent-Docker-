import urllib.request
import json

def get_bilibili_hot_videos():
    url = 'https://api.bilibili.com/x/web-interface/popular?ps=5&rid=1'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            # 【核心修复】：去掉不存在的 vlist，直接读取 list 数组，并切片取前 5 个
            videos = data['data']['list'][:5] 
            for i, video in enumerate(videos, 1):
                print(f"Top {i}: {video['title']}")
    except Exception as e:
        print('Failed to retrieve data:', e)

if __name__ == '__main__':
    get_bilibili_hot_videos()
