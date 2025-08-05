import streamlit as st
import pandas as pd
import zipfile
import io

def process_files(uploaded_files, filters, comment_filter):
    dfs = []
    first = True

    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.zip'):
            # Handle ZIP files
            with zipfile.ZipFile(uploaded_file) as z:
                for filename in z.namelist():
                    if filename.endswith('.csv'):
                        with z.open(filename) as f:
                            try:
                                if first:
                                    df = pd.read_csv(f)
                                    first = False
                                else:
                                    df = pd.read_csv(f, header=None, skiprows=1)
                                    df.columns = dfs[0].columns
                                dfs.append(df)
                            except Exception as e:
                                st.warning(f"Failed to read '{filename}' in zip: {e}")
        elif uploaded_file.name.endswith('.csv'):
            # Handle regular CSVs
            try:
                if first:
                    df = pd.read_csv(uploaded_file)
                    first = False
                else:
                    df = pd.read_csv(uploaded_file, header=None, skiprows=1)
                    df.columns = dfs[0].columns
                dfs.append(df)
            except Exception as e:
                st.warning(f"Failed to read '{uploaded_file.name}': {e}")
        else:
            st.warning(f"Unsupported file type: {uploaded_file.name}")

    if not dfs:
        return None

    combined_df = pd.concat(dfs, ignore_index=True)

    # Apply filters
    if comment_filter:
        combined_df = combined_df[~combined_df['Comment'].str.contains(comment_filter, na=False)]

    if filters:
        pattern = '|'.join(filters)
        combined_df = combined_df[~combined_df['MSG Flight'].str.contains(pattern, na=False)]

    return combined_df

st.title("Data Platform Billing Import Flight Sorter")

uploaded_files = st.file_uploader("Upload CSV or ZIP files", type=['csv', 'zip'], accept_multiple_files=True)

filters = st.text_input("Exclude rows containing these codes in 'MSG Flight' (comma separated):", "SKL,LFT,ZKZ,ZKI,ZKV,ZKN,MDK,FDC,N87,N96,N72,N81,N14,ZKR,N11,VHO,VHX,VHA,ZKX,ZKJ,ZKT,GIS,VHC,XFX,N43")
comment_filter = st.text_input("Exclude rows containing this text in 'Comment':", "Matching flight found, Sendback")

if st.button("Process Files"):
    if not uploaded_files:
        st.warning("Please upload at least one CSV or ZIP file.")
    else:
        filter_list = [x.strip() for x in filters.split(',')] if filters else []
        df = process_files(uploaded_files, filter_list, comment_filter)
        if df is None or df.empty:
            st.warning("No data found after processing.")
        else:
            st.success(f"Found {len(df)} flights:")
            st.dataframe(df)
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
