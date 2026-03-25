import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(
    page_title="Amazon 发货计划生成器 V23",
    page_icon="📦",
    layout="wide"
)

# 隐藏Streamlit的默认菜单和页脚
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("📦 Amazon 发货计划生成器 V23")
st.markdown("---")

# 读取HTML文件内容
html_code = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Amazon 发货计划 - 合并单元格修复+模板记忆版 V23</title>
    <script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #f4f7f6; padding: 30px; margin: 0; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h2 { text-align: center; color: #1890ff; margin-top: 0; }
        .upload-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 25px 0; }
        .upload-box { position: relative; border: 2px dashed #d9d9d9; border-radius: 8px; padding: 20px; text-align: center; background: #fafafa; cursor: pointer; height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .upload-box.active { border-color: #52c41a; background: #f6ffed; }
        .remove-btn { position: absolute; top: 5px; right: 5px; width: 22px; height: 22px; background: #ff4d4f; color: white; border-radius: 50%; display: none; justify-content: center; align-items: center; cursor: pointer; border: none; font-weight: bold; font-size: 14px; }
        .upload-box.active .remove-btn { display: flex; }
        .btn-main { display: block; width: 100%; padding: 15px; background: #1890ff; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-main:hover:not(:disabled) { background: #40a9ff; }
        .btn-main:disabled { background: #d9d9d9; cursor: not-allowed; }
        .history-section { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .history-title { font-size: 13px; font-weight: bold; color: #856404; margin-bottom: 8px; }
        .history-list { display: flex; gap: 10px; flex-wrap: wrap; }
        .history-item { background: white; border: 1px solid #d9d9d9; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: 0.2s; }
        .history-item:hover { border-color: #1890ff; color: #1890ff; }
        .file-name { font-size:11px; color:#999; margin-top:5px; word-break: break-all; }
        p { font-size: 12px; color: #666; text-align: center; margin: 10px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>📦 Amazon 发货计划 (终极逻辑版 V23)</h2>
    <p>兼容合并单元格 | 自动追溯首行数据 | 模板历史记忆</p>
    
    <div class="history-section" id="historyArea" style="display: none;">
        <div class="history-title">🕒 常用空白模板记录 (限2条)</div>
        <div class="history-list" id="historyList"></div>
    </div>

    <div class="upload-section">
        <div class="upload-box" id="boxSource">
            <button class="remove-btn" onclick="clearFile('source', event)">×</button>
            <b>1. 上传数据源汇总表</b>
            <div class="file-name" id="nameSource">支持合并单元格自动填充</div>
            <input type="file" id="fileSource" hidden accept=".xlsx,.xls,.csv">
        </div>
        <div class="upload-box" id="boxTemplate">
            <button class="remove-btn" onclick="clearFile('template', event)">×</button>
            <b>2. 上传空白发货模板</b>
            <div class="file-name" id="nameTemplate">决定导出列顺序</div>
            <input type="file" id="fileTemplate" hidden accept=".xlsx,.xls,.csv">
        </div>
    </div>

    <button id="processBtn" class="btn-main" disabled>🚀 生成导出表</button>
</div>

<script>
    let sourceData = null;
    let templateHeaders = null;
    let tplHistory = JSON.parse(localStorage.getItem('fba_tpl_v23_cache') || "[]");

    const globalStoreMap = {
        "bakatatoyz": { "us": "Bakatatoyz-US", "ca": "Bakatatoyz-CA" },
        "yeonational&toys": { "eu": "YeoNational&Toys-DE", "de": "YeoNational&Toys-DE", "uk": "YeoNational&Toys-UK" },
        "yeonhatoys": { "us": "Yeonha Toys-US", "ca": "Yeonha Toys-CA" },
        "jasnkkont": { "us": "JASNKKONT-US", "ca": "JASNKKONT-CA" },
        "mapixo": { "us": "MAPIXO-US", "ca": "MAPIXO-CA" },
        "uzoxlsn": { "us": "Uzoxlsn-US", "ca": "Uzoxlsn-CA" },
        "moeaws": { "us": "MOEAWS-US", "ca": "MOEAWS-CA" },
        "karberdark": { "us": "KarberDark-US", "ca": "KarberDark-CA" },
        "laxdacee": { "us": "Laxdacee-US", "ca": "Laxdacee-CA" },
        "byonebye": { "us": "Byonebye-US", "ca": "Byonebye-CA" },
        "cawiew": { "us": "CAWIEW-US", "ca": "CAWIEW-CA" },
        "shunhuix": { "de": "SHUNHUIX-DE", "uk": "SHUNHUIX-UK", "eu": "SHUNHUIX-DE" }
    };

    window.onload = () => {
        renderHistory();
        setupUploadBoxes();
    };
    
    function setupUploadBoxes() {
        const sourceBox = document.getElementById('boxSource');
        const templateBox = document.getElementById('boxTemplate');
        const sourceInput = document.getElementById('fileSource');
        const templateInput = document.getElementById('fileTemplate');
        
        sourceBox.addEventListener('click', (e) => {
            if(e.target !== sourceBox.querySelector('.remove-btn')) {
                sourceInput.click();
            }
        });
        
        templateBox.addEventListener('click', (e) => {
            if(e.target !== templateBox.querySelector('.remove-btn')) {
                templateInput.click();
            }
        });
        
        sourceInput.onchange = (e) => handleFile(e.target.files[0], 'source');
        templateInput.onchange = (e) => handleFile(e.target.files[0], 'template');
    }

    function handleFile(file, type) {
        if(!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            const data = new Uint8Array(ev.target.result);
            const wb = XLSX.read(data, {type: 'array'});
            const ws = wb.Sheets[wb.SheetNames[0]];
            if(type === 'source') { 
                sourceData = XLSX.utils.sheet_to_json(ws, {defval: ""}); 
                document.getElementById('boxSource').classList.add('active');
                document.getElementById('nameSource').innerText = file.name;
            } else { 
                const dataRows = XLSX.utils.sheet_to_json(ws, {header: 1});
                if(dataRows.length > 0) {
                    templateHeaders = dataRows[0];
                }
                document.getElementById('boxTemplate').classList.add('active');
                document.getElementById('nameTemplate').innerText = file.name;
                saveTemplate(file.name, templateHeaders);
            }
            checkReady();
        };
        reader.readAsArrayBuffer(file);
    }

    function saveTemplate(name, headers) {
        tplHistory = tplHistory.filter(i => i.name !== name);
        tplHistory.unshift({ name, headers });
        if(tplHistory.length > 2) tplHistory.pop();
        localStorage.setItem('fba_tpl_v23_cache', JSON.stringify(tplHistory));
        renderHistory();
    }

    function renderHistory() {
        const area = document.getElementById('historyArea');
        const list = document.getElementById('historyList');
        if(tplHistory.length === 0) {
            area.style.display = 'none';
            return;
        }
        area.style.display = 'block';
        list.innerHTML = tplHistory.map((item, index) => \`
            <div class="history-item" onclick="applyHistory(\${index})">📄 \${item.name}</div>
        \`).join('');
    }

    function applyHistory(index) {
        templateHeaders = tplHistory[index].headers;
        document.getElementById('boxTemplate').classList.add('active');
        document.getElementById('nameTemplate').innerText = "已加载历史: " + tplHistory[index].name;
        checkReady();
    }

    function checkReady() {
        const btn = document.getElementById('processBtn');
        btn.disabled = !(sourceData && templateHeaders);
    }

    function clearFile(type, e) {
        e.stopPropagation();
        if(type === 'source') { 
            sourceData = null; 
            document.getElementById('boxSource').classList.remove('active'); 
            document.getElementById('nameSource').innerText = "支持合并单元格自动填充";
            document.getElementById('fileSource').value = "";
        } else { 
            templateHeaders = null;
            document.getElementById('boxTemplate').classList.remove('active'); 
            document.getElementById('nameTemplate').innerText = "决定导出列顺序";
            document.getElementById('fileTemplate').value = "";
        }
        checkReady();
    }

    document.getElementById('processBtn').onclick = () => {
        if(!sourceData || !templateHeaders) return;
        
        const finalRows = [];
        let lastAcc = "";
        let lastCnt = "";
        let lastSKU = "";

        sourceData.forEach(row => {
            let currentAcc = String(row['账号'] || "").trim();
            let currentCnt = String(row['国家'] || "").trim();
            let currentSKU = String(row['SKU'] || "").trim();

            if (currentAcc !== "") lastAcc = currentAcc;
            if (currentCnt !== "") lastCnt = currentCnt;
            if (currentSKU !== "") lastSKU = currentSKU;

            const qty = parseFloat(row['自定义发货'] || 0);

            if(qty > 0) {
                let accKey = lastAcc.toLowerCase();
                let cntKey = lastCnt.toLowerCase();
                let storeName = "";

                if (globalStoreMap[accKey] && globalStoreMap[accKey][cntKey]) {
                    storeName = globalStoreMap[accKey][cntKey];
                } else {
                    let displayCnt = (cntKey === "eu") ? "DE" : lastCnt.toUpperCase();
                    storeName = lastAcc + "-" + displayCnt;
                }

                const rawFNSKU = String(row['标签（FNSKU)'] || "").trim();
                let targetMSKU = lastSKU !== "" ? lastSKU : "";

                const newRow = {};
                templateHeaders.forEach(h => {
                    const hn = String(h).trim();
                    if(hn === "*店铺") newRow[h] = storeName;
                    else if(hn.includes("包装类型")) newRow[h] = "原厂包装";
                    else if(hn === "MSKU") newRow[h] = targetMSKU;
                    else if(hn === "FNSKU") newRow[h] = rawFNSKU;
                    else if(hn === "*计划发货量") newRow[h] = qty;
                    else newRow[h] = "";
                });
                finalRows.push(newRow);
            }
        });

        if(finalRows.length === 0) {
            alert("没有找到发货量大于0的记录！");
            return;
        }

        const now = new Date();
        const fileName = `发货计划产品表\${now.getFullYear()}\${String(now.getMonth()+1).padStart(2,'0')}\${String(now.getDate()).padStart(2,'0')}.xlsx`;
        const ws = XLSX.utils.json_to_sheet(finalRows, {header: templateHeaders});
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Upload");
        XLSX.writeFile(wb, fileName);
    };
</script>
</body>
</html>
"""

# 使用components.html显示HTML内容
components.html(html_code, height=800, scrolling=True)

# 添加使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 操作步骤：
    1. **上传数据源汇总表**：包含账号、国家、SKU、标签（FNSKU）、自定义发货等列
    2. **上传空白发货模板**：决定导出文件的列顺序和格式
    3. **点击生成按钮**：自动处理并下载发货计划文件
    
    ### 功能特点：
    - ✅ 支持合并单元格自动填充
    - ✅ 模板历史记忆（最多保存2条）
    - ✅ 自动匹配店铺名称规则
    - ✅ 支持多国家站点映射
    
    ### 注意事项：
    - 发货量必须大于0才会被导出
    - 模板文件的第一行会被作为表头
    - 支持 .xlsx, .xls, .csv 格式
    """)
