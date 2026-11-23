import os
import shutil

# ==========================================
# 1. 設定要處理的資料夾路徑
# ==========================================
TARGET_FOLDER = "./"
BACKUP_FOLDER = "./backup_html_audio_fix"

# ==========================================
# 2. 手機版原生同步語音引擎 (iOS / Android 100% 必響版)
# ==========================================
NEW_AUDIO_LOGIC = """    // --- 手機版原生同步語音引擎 (Web Speech API) ---
    document.addEventListener('click', function(e) {
      if (e.target.classList.contains('play-word')) {
        speakText(e.target.getAttribute('data-text'), 0.9);
      } else if (e.target.classList.contains('play-sentence')) {
        speakText(e.target.getAttribute('data-text'), 1.0);
      }
    });

    function speakText(text, rate) {
      if (!text) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text.split('...').join(' '));
      utterance.lang = 'en-US';
      utterance.rate = rate;
      window.speechSynthesis.speak(utterance);
    }"""

# 舊版可能出現的發音邏輯起點標記（依優先順序尋找）
AUDIO_START_MARKERS = [
    "// --- 音效處理區塊",
    "const globalAudio = new Audio();",
    "document.addEventListener('click', function(e) {"
]

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 尋找起點位置（必須在 createRow 之後，避免誤抓到上方程式碼）
    create_row_idx = content.find("function createRow")
    if create_row_idx == -1:
        return False, "找不到 createRow 函式（非單字表網頁，已安全略過）"

    start_idx = -1
    for marker in AUDIO_START_MARKERS:
        idx = content.find(marker, create_row_idx)
        if idx != -1:
            start_idx = idx
            break

    if start_idx == -1:
        return False, "找不到發音區塊起點，已安全略過"

    # 尋找終點位置：catch (error) 區塊之前
    catch_idx = content.find("} catch (error)", start_idx)
    if catch_idx == -1:
        catch_idx = content.find("} catch (", start_idx)
    if catch_idx == -1:
        return False, "找不到結尾 catch 區塊，已安全略過"

    # 使用「純字串精確切片」替換（完全不使用 re.sub，100% 避免反斜線轉義破壞語法）
    new_content = content[:start_idx] + NEW_AUDIO_LOGIC + "\n\n  " + content[catch_idx:]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True, "成功升級為「手機同步原生語音引擎」"

def main():
    if not os.path.exists(TARGET_FOLDER):
        print(f"錯誤：找不到目錄 '{TARGET_FOLDER}'")
        return

    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    html_files = [
        f for f in os.listdir(TARGET_FOLDER)
        if f.lower().endswith(".html") and not f.lower().startswith("index")
    ]

    if not html_files:
        print("未在目前資料夾找到任何單字 .html 檔案。")
        return

    print(f"找到 {len(html_files)} 個 HTML 檔案，開始安全批次更新...\n" + "-" * 55)
    success_count = 0

    for filename in html_files:
        src_path = os.path.join(TARGET_FOLDER, filename)
        backup_path = os.path.join(BACKUP_FOLDER, filename)

        # 修改前自動建立備份
        shutil.copy2(src_path, backup_path)

        ok, msg = process_file(src_path)
        if ok:
            print(f"✅ {filename} : {msg}")
            success_count += 1
        else:
            print(f"⏩ {filename} : {msg}")

    print("-" * 55)
    print(f"處理完成！共成功更新 {success_count} / {len(html_files)} 個檔案。")
    print(f"原始檔案已全部安全備份至：{os.path.abspath(BACKUP_FOLDER)}")

if __name__ == "__main__":
    main()
