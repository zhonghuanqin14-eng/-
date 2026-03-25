import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Amazon 发货计划生成器", page_icon="📦", layout="wide")

st.title("📦 Amazon 发货计划生成器")
st.markdown("---")

# 初始化session state
if 'data1' not in st.session_state:
    st.session_state.data1 = None
if 'data2' not in st.session_state:
    st.session_state.data2 = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 导出表格 (原始表)")
    file1 = st.file_uploader("上传原始数据表", type=['xlsx', 'xls'], key="file1")
    if file1 is not None:
        try:
            df1 = pd.read_excel(file1)
            st.session_state.data1 = df1
            st.success(f"✅ 已加载: {file1.name}，共 {len(df1)} 行数据")
            st.dataframe(df1.head(3))
        except Exception as e:
            st.error(f"读取失败: {e}")

with col2:
    st.subheader("2. 模板表格 (空模板)")
    file2 = st.file_uploader("上传模板文件", type=['xlsx', 'xls'], key="file2")
    if file2 is not None:
        try:
            df2 = pd.read_excel(file2, header=None)
            st.session_state.data2 = df2
            st.success(f"✅ 已加载模板: {file2.name}")
            st.dataframe(df2.head(5))
        except Exception as e:
            st.error(f"读取失败: {e}")

st.markdown("---")

if st.button("🚀 合并生成发货表", type="primary", use_container_width=True):
    if st.session_state.data1 is None or st.session_state.data2 is None:
        st.error("❌ 请先上传两个表格！")
    else:
        with st.spinner("正在处理数据..."):
            try:
                data1 = st.session_state.data1
                template_headers = st.session_state.data2.iloc[0].astype(str).tolist()
                
                final_rows = []
                processed_count = 0
                skipped_count = 0
                
                for idx, row in data1.iterrows():
                    # 获取发货量
                    qty_val = row.get('发货量', 0)
                    if pd.isna(qty_val):
                        qty = 0
                    else:
                        qty = int(qty_val)
                    
                    if qty > 0:
                        # 处理店铺名称
                        store_name = ""
                        country = str(row.get('国家', '')).lower()
                        cnt_map = {
                            "us": "US", "ca": "CA", "mx": "MX", 
                            "uk": "UK", "de": "DE", "fr": "FR", 
                            "it": "IT", "es": "ES", "jp": "JP", "au": "AU"
                        }
                        
                        account = str(row.get('账号', 'Unknown'))
                        
                        if country in cnt_map:
                            store_name = f"{account}-{cnt_map[country]}"
                        elif country == "eu":
                            store_name = f"{account}-DE"
                        else:
                            store_name = f"{account}-{country.upper()}"
                        
                        # 构建新行
                        new_row = {}
                        for h in template_headers:
                            hn = str(h).strip()
                            if hn == "*店铺":
                                new_row[h] = store_name
                            elif "包装类型" in hn:
                                new_row[h] = "原厂包装"
                            elif hn == "MSKU":
                                new_row[h] = str(row.get('SKU', '')).strip()
                            elif hn == "FNSKU":
                                new_row[h] = str(row.get('标签（FNSKU)', '')).strip()
                            elif hn == "*计划发货量":
                                new_row[h] = qty
                            else:
                                new_row[h] = ""
                        final_rows.append(new_row)
                        processed_count += 1
                    else:
                        if qty == 0:
                            skipped_count += 1
                
                if len(final_rows) == 0:
                    st.warning("⚠️ 没有找到发货量大于0的记录")
                else:
                    result_df = pd.DataFrame(final_rows)
                    
                    # 生成Excel文件
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        result_df.to_excel(writer, sheet_name='ShipPlan', index=False)
                    
                    output.seek(0)
                    
                    # 显示结果
                    st.success(f"✅ 处理完成！共生成 {processed_count} 条发货记录")
                    st.dataframe(result_df.head(10))
                    
                    # 下载按钮
                    today = datetime.now().strftime("%Y%m%d")
                    filename = f"发货计划_{today}.xlsx"
                    
                    st.download_button(
                        label="📥 下载发货计划文件",
                        data=output,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"处理失败: {str(e)}")
                st.exception(e)

st.markdown("---")
st.caption("📌 提示：原始表需要包含'国家'、'账号'、'SKU'、'标签（FNSKU)'、'发货量'等列")
