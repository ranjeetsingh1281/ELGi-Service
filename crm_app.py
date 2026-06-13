# ==========================
# LOCATION BASED MACHINE POPULATION
# ==========================

st.markdown("---")
st.subheader("🌍 Location Based Machine Population")

map_df = master.copy()

# Find City Column
city_col = None

for col in map_df.columns:
    if "city" in str(col).lower():
        city_col = col
        break

if city_col:

    map_df[city_col] = map_df[city_col].astype(str)

    def extract_city(x):
        try:
            parts = str(x).upper().split(",")

            if len(parts) >= 2:
                return parts[1].strip()

            return parts[0].strip()

        except:
            return None

    map_df["MAP_CITY"] = map_df[city_col].apply(extract_city)

    city_summary = (
        map_df.groupby("MAP_CITY")
        .size()
        .reset_index(name="Machine Count")
    )

    city_coordinates = {
        "HAZARIBAGH":[23.9966,85.3691],
        "DHANBAD":[23.7957,86.4304],
        "JAMSHEDPUR":[22.8046,86.2029],
        "RAMGARH":[23.6307,85.5214],
        "RANCHI":[23.3441,85.3096],
        "BOKARO":[23.6693,86.1511],
        "PALAMU":[24.0397,84.0653],
        "DEOGHAR":[24.4820,86.6990],
        "GUMLA":[23.0440,84.5442],
        "LATEHAR":[23.7446,84.5043]
    }

    city_summary["lat"] = city_summary["MAP_CITY"].apply(
        lambda x: city_coordinates.get(x,[None,None])[0]
    )

    city_summary["lon"] = city_summary["MAP_CITY"].apply(
        lambda x: city_coordinates.get(x,[None,None])[1]
    )

    city_summary = city_summary.dropna()

    if not city_summary.empty:

        st.success(
            f"📍 {city_summary['Machine Count'].sum()} Machines Across {len(city_summary)} Cities"
        )

        st.map(
            city_summary.rename(
                columns={
                    "lat":"latitude",
                    "lon":"longitude"
                }
            )
        )

        st.dataframe(
            city_summary.sort_values(
                "Machine Count",
                ascending=False
            ),
            use_container_width=True
        )

    else:

        st.warning(
            "No matching city coordinates found"
        )

else:

    st.error("City column not found in Master sheet")
