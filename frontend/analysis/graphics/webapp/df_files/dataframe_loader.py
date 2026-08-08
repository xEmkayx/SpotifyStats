from frontend.analysis.graphics.webapp.select_statements import allrounder


def reload_df_store():
    # Direct DB query; no CSV cache detour (see dataframe_store.get_default_df).
    return allrounder()
