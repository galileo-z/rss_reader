import feedparser
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
import html

class RSSReader:
    def __init__(self, config_file='rss_config.json'):
        self.config_file = config_file
        self.feeds_data = {}
        self.load_config()

    def load_config(self):
        """从JSON文件加载RSS配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.feeds_data = json.load(f)

    def fetch_feeds(self):
        """获取所有RSS源的内容"""
        all_entries = {}
        for category, feeds in self.feeds_data.items():
            category_entries = []
            for feed_url in feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        # 统一时间格式
                        if hasattr(entry, 'published_parsed'):
                            pub_date = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, 'updated_parsed'):
                            pub_date = datetime(*entry.updated_parsed[:6])
                        else:
                            pub_date = datetime.now()
                        
                        # 确保内容完整性
                        content = ''
                        if hasattr(entry, 'content'):
                            content = entry.content[0].value
                        elif hasattr(entry, 'description'):
                            content = entry.description
                        
                        category_entries.append({
                            'title': entry.title,
                            'link': entry.link,
                            'content': content,
                            'date': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'timestamp': pub_date.timestamp(),
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else feed_url
                        })
                except Exception as e:
                    print(f"Error fetching feed {feed_url}: {str(e)}")
                    continue
            
            all_entries[category] = sorted(
                category_entries,
                key=lambda x: x['timestamp'],
                reverse=True
            )
        
        return all_entries

    def generate_html(self):
        """生成HTML页面"""
        feeds = self.fetch_feeds()
        categories = list(feeds.keys())

        html_template = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Reader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .category-selector {
            margin-bottom: 20px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .feed-item {
            background-color: white;
            margin-bottom: 20px;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .feed-header {
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .feed-title {
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #2962ff;
            text-decoration: none;
        }
        .feed-title:hover {
            text-decoration: underline;
        }
        .feed-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .feed-content {
            line-height: 1.6;
            display: none;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .feed-content.expanded {
            display: block;
        }
        .feed-content img {
            max-width: 100%;
            height: auto;
        }
        select {
            padding: 8px;
            font-size: 16px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .hidden {
            display: none;
        }
        .toggle-indicator {
            font-size: 1.2em;
            color: #666;
            transition: transform 0.3s ease;
        }
        .toggle-indicator.expanded {
            transform: rotate(180deg);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="category-selector">
            <select id="categorySelect" onchange="changeCategory()">
        """

        # 添加分类选项
        for category in categories:
            html_template += f'<option value="{category}">{category}</option>\n'

        html_template += """
            </select>
        </div>
        """

        # 添加每个分类的内容
        for category in categories:
            html_template += f'<div id="{category}" class="category-content hidden">\n'
            for i, entry in enumerate(feeds[category]):
                html_template += f"""
                <div class="feed-item">
                    <div class="feed-header" onclick="toggleContent('{category}-{i}')">
                        <div>
                            <div class="feed-title">{entry['title']}</div>
                            <div class="feed-meta">
                                <span>{entry['source']} • {entry['date']}</span>
                            </div>
                        </div>
                        <span class="toggle-indicator" id="indicator-{category}-{i}">▼</span>
                    </div>
                    <div id="content-{category}-{i}" class="feed-content">
                        <div class="feed-content-inner">
                            {entry['content']}
                        </div>
                        <div style="margin-top: 15px;">
                            <a href="{entry['link']}" target="_blank">阅读原文</a>
                        </div>
                    </div>
                </div>
                """
            html_template += '</div>\n'

        html_template += """
    </div>
    <script>
        function changeCategory() {
            const select = document.getElementById('categorySelect');
            const category = select.value;
            document.querySelectorAll('.category-content').forEach(elem => {
                elem.classList.add('hidden');
            });
            document.getElementById(category).classList.remove('hidden');
        }

        function toggleContent(id) {
            const content = document.getElementById('content-' + id);
            const indicator = document.getElementById('indicator-' + id);
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                indicator.classList.remove('expanded');
            } else {
                content.classList.add('expanded');
                indicator.classList.add('expanded');
            }
        }

        // 初始化显示第一个分类
        window.onload = function() {
            const firstCategory = document.getElementById('categorySelect').value;
            document.getElementById(firstCategory).classList.remove('hidden');
        }
    </script>
</body>
</html>
        """

        with open('rss_reader.html', 'w', encoding='utf-8') as f:
            f.write(html_template)

if __name__ == "__main__":
    reader = RSSReader()
    reader.generate_html()