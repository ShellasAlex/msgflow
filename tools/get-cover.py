#!/usr/bin/env python3
"""从文章内容提取关键词，搜索 Unsplash 返回 16:9 封面图 URL"""
import sys, os, json, urllib.request, urllib.parse

def get_keywords(text):
    mapping = {
        'AI': 'artificial intelligence', 'Agent': 'AI agent',
        '代码': 'coding', '技术': 'technology', '写作': 'writing',
        '数据': 'data', '分析': 'analysis', '工具': 'tools',
        '自动': 'automation', '机器人': 'robot', '模型': 'model',
        '智能': 'intelligence', '协作': 'collaboration', '编程': 'programming',
    }
    words = [v for k, v in mapping.items() if k in text]
    return '+'.join(words[:3]) if words else 'technology+digital'

def search_cover(keywords, api_key):
    url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(keywords)}&orientation=landscape&per_page=1"
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get('results', [])
            if results:
                return results[0]['urls']['regular']
    except:
        pass
    return ""

if __name__ == "__main__":
    api_key = os.environ.get("UNSPLASH_KEY", "")
    if not api_key:
        sys.exit(0)

    text = sys.stdin.read()[:500]
    keywords = get_keywords(text)
    url = search_cover(keywords, api_key)
    if url:
        print(url)
