import urllib.request
import json
import os
import datetime

# 接口地址，注意这里的 n=8 会返回8天数据，原Java中 day1Url n=1，day8Url n=8
# 因为是要定期执行，我们拉取当天的即可，如果有漏跑，拉取历史也能兜底
BING_URL = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&video=1"
BASE_DIR = "./data"
IMAGE_DIR = os.path.join(BASE_DIR, "image")
VIDEO_DIR = os.path.join(BASE_DIR, "video")
VIDEO_HD_DIR = os.path.join(BASE_DIR, "video_hd")
VIDEO_MOBILE_DIR = os.path.join(BASE_DIR, "video_mobile")

# 创建目录
for d in [IMAGE_DIR, VIDEO_DIR, VIDEO_HD_DIR, VIDEO_MOBILE_DIR]:
    os.makedirs(d, exist_ok=True)

def download_file(url, file_path):
    if not url: return
    if os.path.exists(file_path):
        print(f"File exists, skip download: {file_path}")
        return
        
    if url.startswith('/'):
        url = "https://cn.bing.com" + url
        
    try:
        print(f"Downloading {url} to {file_path}")
        # 添加 User-Agent 防止被拦截
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print("Success")
    except Exception as e:
        print(f"Download failed: {url} -> {file_path}")
        print(e)

def main():
    try:
        req = urllib.request.Request(BING_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        images = data.get('images', [])
        if not images:
            print("No images found in response")
            return
            
        today = datetime.date.today()
        
        # 遍历返回的图片数据 (最高8条)
        for i in range(len(images)):
            img_info = images[i]
            # 计算对应的日期
            date_str = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 1. 下载图片
            if img_info.get('url'):
                download_file(img_info['url'], os.path.join(IMAGE_DIR, f"{date_str}.jpg"))
                
            # 2. 下载不同清晰度的视频
            # Bing 的 JSON 返回格式中，视频信息放在 vid 字段内
            # 原 Java 代码中的字段对应关系：
            # mp4Url -> vid.sources 中的第一个 MP4
            # mp4HdUrl -> 高清 MP4
            # mp4MobileUrl -> 移动端 MP4
            vid = img_info.get('vid', {})
            if isinstance(vid, dict) and 'sources' in vid:
                sources = vid['sources']
                # Bing 视频 sources 通常形如 [["video/mp4", "url1"], ["video/mp4", "url2"]]
                # 按照之前 Java 的习惯，我们尝试根据特征或顺序来推断
                # 如果找不到具体的区分标志，这里简单将所有返回的 mp4 按顺序对应为普通、高清、移动
                mp4_urls = []
                for src in sources:
                    if len(src) >= 3 and 'mp4' in src[2].lower():
                        mp4_urls.append(src[2])
                    elif len(src) >= 2 and 'mp4' in src[0].lower():
                        mp4_urls.append(src[1])
                
                # 如果有找到 MP4
                if len(mp4_urls) > 0:
                    # 原本对应的3种类型，如果没有3个，就按顺序尽量匹配
                    # 1. 普通视频
                    download_file(mp4_urls[0], os.path.join(VIDEO_DIR, f"{date_str}.mp4"))
                    
                    if len(mp4_urls) > 1:
                        # 2. HD高清视频
                        download_file(mp4_urls[1], os.path.join(VIDEO_HD_DIR, f"{date_str}_hd.mp4"))
                        
                    if len(mp4_urls) > 2:
                        # 3. Mobile移动端视频
                        download_file(mp4_urls[2], os.path.join(VIDEO_MOBILE_DIR, f"{date_str}_m.mp4"))

    except Exception as e:
        print("Spider failed:")
        print(e)

if __name__ == "__main__":
    main()
