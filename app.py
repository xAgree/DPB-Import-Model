import streamlit as st
import pandas as pd
import zipfile
import io
import os

def process_files(uploaded_files, filters, comment_filter):
    dfs = []
    first = True

    for uploaded_file in uploaded_files:
        # Check if ZIP file
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                for filename in z.namelist():
                    if filename.endswith('.csv'):
                        with z.open(filename) as f:
                            if first:
                                df = pd.read_csv(f)
                                first = False
                            else:
                                df = pd.read_csv(f, header=None, skiprows=1)
                                df.columns = dfs[0].columns
                            dfs.append(df)
        else:
            # Single CSV file
            if first:
                df = pd.read_csv(uploaded_file)
                first = False
            else:
                df = pd.read_csv(uploaded_file, header=None, skiprows=1)
                df.columns = dfs[0].columns
            dfs.append(df)

    if not dfs:
        return None

    combined_df = pd.concat(dfs, ignore_index=True)

    if comment_filter:
        combined_df = combined_df[~combined_df['Comment'].str.contains(comment_filter, na=False)]

    if filters:
        pattern = '|'.join(filters)
        combined_df = combined_df[~combined_df['MSG Flight'].str.contains(pattern, na=False)]

    return combined_df

st.title("CSV Merger and Filter")

uploaded_files = st.file_uploader("Upload CSV or ZIP files", type=['csv', 'zip'], accept_multiple_files=True)

filters = st.text_input("Exclude rows containing these codes in 'MSG Flight' (comma separated):", "SKL,LFT,ZKZ,ZKN,MDK,FDC,N87")
comment_filter = st.text_input("Exclude rows containing this text in 'Comment':", "Matching flight found")

if st.button("Process Files"):
    if not uploaded_files:
        st.warning("Please upload at least one CSV or ZIP file.")
    else:
        filter_list = [x.strip() for x in filters.split(',')] if filters else []
        df = process_files(uploaded_files, filter_list, comment_filter)
        if df is None or df.empty:
            st.warning("No data found after processing.")
        else:
            st.success(f"Processed {len(df)} rows.")

            # Convert to Excel in-memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='FilteredData')
            output.seek(0)

            st.download_button(
                label="Download filtered Excel",
                data=output,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
st.dataframe(df)
