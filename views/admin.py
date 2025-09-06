import streamlit as st
import warnings
from datetime import date
import logging
from db.db_utils import execute_query, add_state, add_location, add_sku, add_posm, disable_user, add_region

logging.basicConfig(filename='app.log', level=logging.ERROR)


st.info("⚙ Admin Backend")
st.markdown("""<hr class="line">""",unsafe_allow_html=True) 

setup_fields= st.sidebar.expander("⚙ :blue[Admin Backend Setup Fields]", expanded=True)
with setup_fields:
        st.caption("Use this section to manage regions, states, locations, SKUs, POSMs, and user accounts.")
        selection=st.selectbox("Select Setup Section", 
        ["Regions","States","Locations","SKUs","POSMs","Users","Location By Region"], key="admin_setup_section")
if selection == "Regions":
    region, regiontable= st.columns([4,3], gap="small",vertical_alignment="top")
        # Manage States
    with region:
        with st.expander("Manage and Create a promassidor Region", expanded=True):
            new_region = st.text_input("Add Region")
            if st.button("Add Region"):
                try:
                    add_region(new_region)
                    st.success(f"Region {new_region} added successfully.")
                except Exception as e:
                    st.error(f"Error adding region: {e}")
            with regiontable:
                st.write("🗺 **:green[Existing Region]**")
                region= execute_query("SELECT * FROM region")
                st.dataframe(region)
                st.caption("Click on a Region to view actual state", unsafe_allow_html=True)
if selection == "States":
     
    state, statetable= st.columns([4,3], gap="small",vertical_alignment="top")
        # Manage States
    with state:
        with st.expander("Manage and Create a state States", expanded=True):
            new_state = st.text_input("Add State")
            if st.button("Add State"):
                try:
                        add_state(new_state)
                        st.success(f"State {new_state} added successfully.")
                except Exception as e:
                        st.error(f"Error adding state: {e}")
                # add_state(new_state)
            with statetable:
                st.write("🗺 **:green[Existing States]**")
                try:
                    states = execute_query("SELECT * FROM states")
                    st.dataframe(states)
                    st.caption("Click on a state to view its locations", unsafe_allow_html=True) 
                except Exception as e:
                    st.error(f"Error fetching states: {e}")     

    st.markdown("""<hr class="topline">""",unsafe_allow_html=True)  

if selection == "Locations":
    # Manage Locations
    location, location_table=st.columns([4,3],gap='medium',vertical_alignment='top')
    with location:
        with st.expander("Manage Locations", expanded=True):
            states = execute_query("SELECT * FROM states")
            state_dict = {s['name']: s['id'] for s in states}
            state_name = st.selectbox("State", list(state_dict.keys()))
            state_id = state_dict[state_name]
            new_loc = st.text_input("Add Location")
            if st.button("Add Location"):
                try:
                    add_location(state_id, new_loc)
                    st.success(f"Location {new_loc} added to {state_name} successfully.")
                except Exception as e:
                    st.error(f"Error adding location: {e}")
                # add_location(state_id, new_loc)
            with location_table:
                try:
                    st.write(f"🗺 **:green[Locations in {state_name}]**")
                    locs = execute_query("SELECT * FROM locations WHERE state_id = %s", (state_id,))
                    st.dataframe(locs)
                    st.caption("Click on a location to view its outlets", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error fetching locations: {e}")
if selection == "Location By Reion":
    # Manage Locations
    location, location_table=st.columns([4,3],gap='medium',vertical_alignment='top')
    with location:
        with st.expander("Manage Locations", expanded=True):
            states = execute_query("SELECT * FROM states")
            state_dict = {s['name']: s['id'] for s in states}
            state_name = st.selectbox("State", list(state_dict.keys()))
            state_id = state_dict[state_name]
            new_loc = st.text_input("Add Location")
            if st.button("Add Location"):
                try:
                    add_location(state_id, new_loc)
                    st.success(f"Location {new_loc} added to {state_name} successfully.")
                except Exception as e:
                    st.error(f"Error adding location: {e}")
                # add_location(state_id, new_loc)
            with location_table:
                try:
                    st.write(f"🗺 **:green[Locations in {state_name}]**")
                    locs = execute_query("SELECT * FROM locations WHERE state_id = %s", (state_id,))
                    st.dataframe(locs)
                    st.caption("Click on a location to view its outlets", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error fetching locations: {e}")


    st.markdown("""<hr class="line">""",unsafe_allow_html=True)  

if selection == "SKUs":
    # Manage SKUs (with category)
    sku, sku_table=st.columns([4,3],gap='medium',vertical_alignment='top')
    with sku:
        with st.expander("Manage SKUs", expanded=True):
            category = st.text_input("Category (e.g., Seasoning)")
            name = st.text_input("SKU Name (e.g., Onga Cubes chicken 50g *4)")
            desc = st.text_area("Description")
            expiry = st.checkbox("Track Expiry")
            if st.button("Add SKU"):
                try:
                    add_sku(category, name, desc, expiry)
                    st.success(f"SKU {name} added successfully.")   
                except Exception as e:
                    st.error(f"Error adding SKU: {e}")
                # add_sku(category, name, desc, expiry)

            with sku_table:
                try:
                    st.write("🗃 **:green[Existing SKUs]**")
                    skus = execute_query("SELECT * FROM skus")
                    st.dataframe(skus)
                    st.caption("Click on a SKU to view details", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error fetching SKUs: {e}")

    st.markdown("""<hr class="line">""",unsafe_allow_html=True)  

if selection == "POSMs":
    # Manage POSMs
    posms,posms_table=st.columns([4,3],gap='medium',vertical_alignment='top')
    with posms:
        with st.expander("Manage POSMs", expanded=True):
                new_posm = st.text_input("Add POSM (e.g., Display Stand)")
                if st.button("Add POSM"):
                    try:
                        add_posm(new_posm)
                        st.success(f"POSM {new_posm} added successfully.")
                    except Exception as e:
                        st.error(f"Error adding POSM: {e}")
                    # add_posm(new_posm)
                with posms_table: 
                    try:
                        st.write("📦 **:green[Existing POSMs]**")
                        posms = execute_query("SELECT * FROM posms")
                        st.dataframe(posms)
                        st.caption("Click on a POSM to view details", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error fetching POSMs: {e}")

    st.markdown("""<hr class="line">""",unsafe_allow_html=True) 
    # View POSM Deployments
    with st.expander("View POSM Deployments"):
        deployments = execute_query("""
            SELECT pd.id, o.name AS outlet_name, u.email AS user_email, pd.deployed_posms, pd.deployed_at
            FROM posm_deployments pd
            JOIN outlets o ON pd.outlet_id = o.id
            JOIN users u ON pd.deployed_by_user_id = u.id
        """)
        posm_dict = {p['id']: p['name'] for p in execute_query("SELECT * FROM posms")}
        for dep in deployments:
            posm_details = []
            for posm in dep['deployed_posms']:
                posm_name = posm_dict.get(posm['posm_id'], "Unknown")
                quantity = posm['quantity']
                posm_details.append(f"{posm_name}: {quantity}")
            st.write(f"Deployment ID: {dep['id']}, Outlet: {dep['outlet_name']}, User: {dep['user_email']}, "
                     f"POSMs: {', '.join(posm_details)}, Time: {dep['deployed_at']}")

if selection == "Users":
    # Manage Users
    mg_users,mg_users_table=st.columns([4,3],gap='medium',vertical_alignment='top')
    with mg_users:
        with st.expander("Manage Users", expanded=True):
                users = execute_query("SELECT id, email, role, is_active FROM users WHERE role != 'admin'")
                for user in users:
                    col1, col2 = st.columns([3,1], gap="small",vertical_alignment="center")
                    col1.write(f"{user['email']} ({user['role']}) - Active: {user['is_active']}")
                    if col2.button("Disable", key=f"disable_{user['id']}"):
                        disable_user(user['id'])

                        with mg_users_table:
                            try:
                                st.write("👥 **:green[User Accounts]**")
                                st.success(f"User {user['email']} disabled")
                                st.dataframe(users)
                                st.caption("Click on a user to view details", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error fetching users: {e}")