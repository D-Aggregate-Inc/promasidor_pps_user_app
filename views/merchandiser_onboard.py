from numpy import place
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_outlet, get_outlet_by_phone_contact,get_locations_by_user_region
from utils.spaces import upload_image
import warnings
import logging
import phonenumbers
from phonenumbers import carrier

logging.basicConfig(level=logging.INFO)

warnings.filterwarnings('ignore')

st.write(":material/local_convenience_store:**:orange[Outlet Onboarding]**")
@st.cache_data(show_spinner=False, persist='disk')
def banks():
    bank=execute_query("SELECT * FROM banks")
    return bank

user_id = st.session_state['user']['id']

st.markdown("""<hr class="line">""",unsafe_allow_html=True)
st.write(f'Welcome, **:blue[{st.session_state["user"]["email"]}]**! Use the form below to onboard a new outlet.')
st.info("Please click on GPS button to get your location GPS")
location = streamlit_geolocation()
with st.expander("Input Outlet Information",expanded=True):
    st.write(f":material/add_business: :blue[Outlet Basic Information]")
    name = st.text_input("Outlet Name", max_chars=50, help="E.g DM Ventures",placeholder="Enter outlet name")
    phone_contact = st.text_input("Contact Phone", max_chars=11, help="11-digit phone number",placeholder="08012345678")
    if phone_contact and phone_contact.startswith('0') and len(phone_contact)==11:
            formatted_phone = '+234' + phone_contact[1:]
            try:
                parsed_number = phonenumbers.parse(formatted_phone, "NG")
                telco = st.caption(f":blue[The phone number 📲 line is {carrier.name_for_number(parsed_number, "en")}]") if phonenumbers.is_valid_number(parsed_number) else "Unknown"
            except phonenumbers.NumberParseException:
                telco = st.caption("Phone Number Not a Nigeria Number")
    else:
        st.caption("⚠:yellow[Please write a correct and accrate phone number]")
    outlet_number = st.text_input("Shop Number", max_chars=20, help="E.g No. 12, Shop 34B")
    outlet_address = st.text_area("Address", max_chars=200, help="E.g 12, Shop 34B, Tipper Garage Road")
    outlet_landmark = st.text_input("Landmark ", max_chars=50, help="E.g Opposite Tipper Garage, Near Shoprite Mall")
    region_query=execute_query(f"SELECT merchandiser_region FROM users WHERE id = '{user_id}'")
    region=region_query[0]['merchandiser_region']
    st.badge(F"Your PPS region is {region}", icon=":material/location_on:",color='green')
    st.caption(":material/explore_nearby: :blue[Select your market or neighbourhood of the outlet]")
    locations = get_locations_by_user_region(user_id)
    location_dict = {f"{loc['name']} ({loc['region_name']})": loc['id'] for loc in locations}
    location_name = st.selectbox("Location", list(location_dict.keys()) if location_dict else ["No locations available"])
    location_id = location_dict.get(location_name)
    # region_query= execute_query("SELECT * FROM region")
    # region_dict = {r['name']: r['id'] for r in region_query}  
    # region = st.selectbox("Region", list(region_dict.keys()))
    # # state=execute_query("SELECT * FROM states")
    # locations_by_region=execute_query(f"SELECT l.id, l.name as loc_name, r.name as regions FROM locations_by_region l JOIN region r ON l.region_id=r.id WHERE r.name='{region}'")
    # if locations_by_region:
    #         loc_dict={l['loc_name']: l['id'] for l in locations_by_region}
    #         loc_selection=st.selectbox("Location By Regions",list(loc_dict.keys()))
    #         location_id=loc_dict[loc_selection]
    # else:
    #     st.error("Ensure Promasidor Region is setup by Admin")
    # locations = execute_query("SELECT l.id, l.name, s.name as state FROM locations l JOIN states s ON l.state_id = s.id")
    # loc_dict = {f"{loc['state']} - {loc['name']}": loc['id'] for loc in locations}
    # loc_selection = st.selectbox("Location", list(loc_dict.keys()))
    # location_id = loc_dict[loc_selection]
    contact_person=st.text_input("Contact Person", max_chars=50, help="E.g John Doe",placeholder="Enter contact person name")
    classification = st.selectbox("Channel", ['Neighborhood','Open market'])
    if classification=="Neighborhood":
        outlet_type = st.selectbox("Outlet Type NB", ['GSM-Groceries', 'Kiosks', 
                        'Table Tops', 'Table Top-OSC', 
                        ],key=f'{classification}_chosen_{name}_{location_id}_NB')
    elif classification=="Open market":
        outlet_type = st.selectbox("Outlet Type OM", ['Lock-Up Shop(Seasoning)','Lock-Up Shop(Dairy/Beverages)',
                      'Kiosk-(Seasoning)','Kiosk(Dairy/Beverages)',
                      'Table-Top(Seasoning)','Table-Top(Dairy/Beverages)'
                        ],key=f'{classification}_chosen_{name}_{location_id}_OM')
    
    image = st.camera_input("Capture Outlet Image", help="Image is required")
# 
    #account detail info
    st.info(":material/account_balance: Account Information of Outlet Owner")
    account_no=st.text_input("Account Number", max_chars=10, help="10-digit account number",placeholder="8012345678")
    bank_query=banks()
    bank_dict = {b['name']: b['id'] for b in bank_query}  
    bank_name = st.selectbox("Banks", list(bank_dict.keys()))
    account_name=st.text_input("Account Name", max_chars=200, help="Akeusola Chukuemeka Haruna")
    if location and location['latitude'] is not None:
        gps_lat = location['latitude']
        gps_long = location['longitude']
        st.info(f"📍GPS Captured: Lat {gps_lat}, Long {gps_long}")
    else:
        st.warning("Waiting for GPS location...")
        gps_lat, gps_long = None, None  
      
    if st.button("Submit Outlet Onboarded",type='primary') and gps_lat and image and name and outlet_address and bank_name and account_no and outlet_number and classification and phone_contact and account_name and location_id:
        # image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')
        image_key = upload_image(image.getvalue(), folder='outlets', gps_lat=gps_lat, gps_long=gps_long)
        if image_key:
            if get_outlet_by_phone_contact(phone_contact):
                st.warning("😡An outlet with this contact phone already exists.:red[Outlet Info Failed To Submit]")
            else:
                add_outlet(name,location_id, classification,outlet_type, user_id, gps_lat, gps_long, image_key,
                        phone_contact, outlet_number, outlet_address,outlet_landmark, contact_person,region,account_no,bank_name,account_name)
                    
                st.success("Outlet Onboarded Successfully!")
        else:
            st.error("⁉ Pls Ensure all the required field are properly filled and image is taking. Please try again.")
    # elif  not gps_lat:
    #     st.warning("GPS location is required to onboard an outlet.")
    # elif not image:
    #     st.error("Outlet image is required to onboard an outlet.")
