import streamlit as st
import mysql.connector
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
import streamlit.components.v1 as components
import random

st.set_page_config(
    page_title="Wildfire Reporting System",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    'primary': '#d97706',      # Warm orange (fire)
    'secondary': '#92400e',    # Dark orange/brown
    'accent1': '#fbbf24',      # Golden yellow
    'accent2': '#dc2626',      # Red (danger)
    'neutral': '#78716c'       # Warm gray
}

DB_CONFIG = {
    'host': 'sql12.freesqldatabase.com',
    'database': 'sql12798735',
    'user': 'sql12798735',
    'password': 'dgZDgZImeT',
    'port': 3306
}

# Educational content for flashcards and game
EDUCATIONAL_CONTENT = {
    "forest_protection": [
        {
            "title": "Create Defensible Space",
            "content": "Clear vegetation within 30 feet of structures. Remove dead plants, grass, and weeds. Trim tree branches to 6 feet from the ground.",
            "icon": "🌲"
        },
        {
            "title": "Use Fire-Resistant Plants",
            "content": "Plant fire-resistant species like lavender, rosemary, and succulents. Avoid highly flammable plants like juniper and pine.",
            "icon": "🌿"
        },
        {
            "title": "Maintain Equipment",
            "content": "Keep lawn mowers and chainsaws well-maintained. Use spark arresters on equipment. Avoid using equipment during high-risk periods.",
            "icon": "🔧"
        },
        {
            "title": "Proper Disposal",
            "content": "Never burn debris during dry conditions. Dispose of cigarettes properly. Store flammable materials safely away from heat sources.",
            "icon": "🚮"
        }
    ],
    "wildfire_location": [
        {
            "title": "Stay Low and Move Fast",
            "content": "If trapped, find the nearest body of water or cleared area. Stay low to avoid smoke inhalation. Cover nose and mouth with cloth.",
            "icon": "🏃‍♂️"
        },
        {
            "title": "Call for Help",
            "content": "Call 911 immediately. Give your exact location. Stay on the line and follow dispatcher instructions.",
            "icon": "📞"
        },
        {
            "title": "Find Safe Shelter",
            "content": "Seek shelter in a building or vehicle. Close all windows and vents. Turn on headlights and hazard lights if in a car.",
            "icon": "🏠"
        },
        {
            "title": "Avoid Dangerous Areas",
            "content": "Stay away from canyons and steep slopes where fire moves faster. Avoid areas with heavy vegetation or dead trees.",
            "icon": "⚠️"
        }
    ],
    "fire_nearby": [
        {
            "title": "Monitor Conditions",
            "content": "Listen to emergency broadcasts. Watch for evacuation orders. Keep emergency kit ready and vehicle fueled.",
            "icon": "📻"
        },
        {
            "title": "Prepare to Evacuate",
            "content": "Pack important documents, medications, and essentials. Have multiple evacuation routes planned. Don't wait for official orders if you feel unsafe.",
            "icon": "🎒"
        },
        {
            "title": "Protect Your Home",
            "content": "Close all windows and doors. Remove flammable materials from around your house. Turn on sprinklers if available.",
            "icon": "🏡"
        },
        {
            "title": "Stay Informed",
            "content": "Follow local emergency services on social media. Sign up for emergency alerts. Keep battery-powered radio handy.",
            "icon": "📱"
        }
    ],
    "survivor_locations": [
        {
            "title": "Emergency Shelters",
            "content": "Red Cross shelters provide temporary housing, food, and basic medical care. Schools and community centers often serve as evacuation centers.",
            "icon": "🏫"
        },
        {
            "title": "Hospitals and Clinics",
            "content": "Medical facilities provide treatment for burns, smoke inhalation, and other injuries. Many offer emergency services 24/7.",
            "icon": "🏥"
        },
        {
            "title": "Relief Centers",
            "content": "Disaster relief organizations provide food, water, clothing, and financial assistance. Salvation Army and local churches often help.",
            "icon": "🤝"
        },
        {
            "title": "Safe Zones",
            "content": "Large parking lots, beaches, and open fields away from vegetation. Sports stadiums and fairgrounds often serve as gathering points.",
            "icon": "🏟️"
        }
    ],
    "future_improvements": [
        {
            "title": "Verified User Login",
            "content": "We plan to introduce a secure login system with verified user accounts. This will allow citizens, emergency responders, and trusted organizations to access personalized dashboards, submit verified reports, and manage their data with enhanced security.",
            "icon": "👤"
        },
        {
            "title": "Smart Alerts System",
            "content": "Our future vision includes sending real-time alerts to users if a wildfire is reported near their location. Using location data, the system will notify individuals within a danger radius through in-app notifications, SMS, or email.",
            "icon": "📡"
        }
    ]
}

def get_db_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

def create_wildfire_report(data):
    """Insert new wildfire report into database"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO wildfire_reports 
            (reporter_name, reporter_email, reporter_phone, latitude, longitude, 
             location_description, fire_size, severity, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, data)
            report_id = cursor.lastrowid
            
            # Create notification for new report
            severity_level = data[7]  # severity is at index 7
            notification_type = 'Alert' if severity_level == 'Critical' else 'New Report'
            notification_message = f"New wildfire reported: {data[6]} severity in {data[5]}"
            
            notification_query = """
            INSERT INTO notifications (report_id, message, notification_type)
            VALUES (%s, %s, %s)
            """
            cursor.execute(notification_query, (report_id, notification_message, notification_type))
            
            connection.commit()
            return True
        except mysql.connector.Error as err:
            st.error(f"Error creating report: {err}")
            return False
        finally:
            connection.close()
    return False

def get_wildfire_reports():
    """Fetch all wildfire reports from database"""
    connection = get_db_connection()
    if connection:
        try:
            query = """
            SELECT id, reporter_name, latitude, longitude, location_description, 
                   fire_size, severity, description, reported_at, status, verified
            FROM wildfire_reports 
            ORDER BY reported_at DESC
            """
            df = pd.read_sql(query, connection)
            return df
        except mysql.connector.Error as err:
            st.error(f"Error fetching reports: {err}")
            return pd.DataFrame()
        finally:
            connection.close()
    return pd.DataFrame()

def get_notifications():
    """Fetch recent notifications"""
    connection = get_db_connection()
    if connection:
        try:
            query = """
            SELECT n.message, n.notification_type, n.created_at, n.is_read,
                   w.location_description, w.severity
            FROM notifications n
            JOIN wildfire_reports w ON n.report_id = w.id
            ORDER BY n.created_at DESC
            LIMIT 10
            """
            df = pd.read_sql(query, connection)
            return df
        except mysql.connector.Error as err:
            st.error(f"Error fetching notifications: {err}")
            return pd.DataFrame()
        finally:
            connection.close()
    return pd.DataFrame()

def create_map(reports_df):
    """Create folium map with wildfire markers"""
    if reports_df.empty:
        # Default map centered on California
        m = folium.Map(location=[36.7783, -119.4179], zoom_start=6, tiles='OpenStreetMap', attr='OpenStreetMap')
        return m
    
    # Center map on average coordinates
    center_lat = reports_df['latitude'].mean()
    center_lon = reports_df['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='OpenStreetMap', attr='OpenStreetMap')
    
    severity_colors = {
        'Low': COLORS['accent1'],      # Golden yellow
        'Medium': COLORS['primary'],   # Orange
        'High': COLORS['secondary'],   # Dark orange
        'Critical': COLORS['accent2']  # Red
    }
    
    # Add markers for each report
    for _, report in reports_df.iterrows():
        color = severity_colors.get(report['severity'], COLORS['neutral'])
        
        popup_text = f"""
        <b>Location:</b> {report['location_description']}<br>
        <b>Reporter:</b> {report['reporter_name']}<br>
        <b>Severity:</b> {report['severity']}<br>
        <b>Size:</b> {report['fire_size']}<br>
        <b>Status:</b> {report['status']}<br>
        <b>Reported:</b> {report['reported_at']}<br>
        <b>Description:</b> {report['description'][:100]}...
        """
        
        folium.CircleMarker(
            location=[report['latitude'], report['longitude']],
            radius=10 if report['severity'] != 'Critical' else 15,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    return m

def get_user_location():
    """Enhanced location detection with proper form integration"""
    location_html = f"""
    <div style="background: linear-gradient(135deg, {COLORS['accent2']}, {COLORS['secondary']}); padding: 2rem; border-radius: 20px; margin: 2rem 0; color: white; box-shadow: 0 10px 40px rgba(220, 38, 38, 0.3);">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.4rem; font-weight: 700; text-align: center;">📍 Location Detection</h4>
        <p id="location-status" style="margin: 1rem 0; font-size: 1.1rem; text-align: center;">🔍 Click button to detect location...</p>
        <p id="coords-display" style="margin: 1rem 0; font-weight: 600; font-size: 1rem; text-align: center;"></p>
        <div style="text-align: center;">
            <button onclick="useMyLocation()" style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['accent1']}); color: white; border: none; padding: 1.2rem 2.5rem; border-radius: 16px; font-weight: 700; cursor: pointer; font-size: 1.1rem; box-shadow: 0 8px 25px rgba(217, 119, 6, 0.4); transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px;">
                📍 Use My Current Location
            </button>
        </div>
    </div>
    
    <script>
    function useMyLocation() {{
        if (navigator.geolocation) {{
            document.getElementById("location-status").innerHTML = "🔍 Getting your location...";
            navigator.geolocation.getCurrentPosition(
                function(position) {{
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    document.getElementById("location-status").innerHTML = "✅ Location detected successfully!";
                    document.getElementById("coords-display").innerHTML = 
                        `📍 Coordinates: ${{lat.toFixed(6)}}, ${{lon.toFixed(6)}}`;
                    
                    setTimeout(() => {{
                        const parentDoc = window.parent.document;
                        const numberInputs = parentDoc.querySelectorAll('input[type="number"]');
                        
                        if (numberInputs.length >= 2) {{
                            // First number input is latitude, second is longitude
                            const latInput = numberInputs[0];
                            const lonInput = numberInputs[1];
                            
                            // Clear and set values
                            latInput.value = lat.toFixed(6);
                            lonInput.value = lon.toFixed(6);
                            
                            // Trigger change events
                            latInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            lonInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            latInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            lonInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            
                            document.getElementById("location-status").innerHTML = "✅ Location filled in form!";
                        }} else {{
                            document.getElementById("location-status").innerHTML = 
                                `⚠️ Please enter manually: ${{lat.toFixed(6)}}, ${{lon.toFixed(6)}}`;
                        }}
                    }}, 1000);
                }},
                function(error) {{
                    let message = "";
                    switch(error.code) {{
                        case error.PERMISSION_DENIED:
                            message = "❌ Location access denied. Please enable location services.";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = "❌ Location information unavailable.";
                            break;
                        case error.TIMEOUT:
                            message = "❌ Location request timed out.";
                            break;
                        default:
                            message = "❌ Unknown error occurred.";
                            break;
                    }}
                    document.getElementById("location-status").innerHTML = message;
                }},
                {{
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }}
            );
        }} else {{
            document.getElementById("location-status").innerHTML = "❌ Geolocation not supported by this browser.";
        }}
    }}
    </script>
    """
    return location_html

def create_flashcard_game():
    """Create interactive flashcard game"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); padding: 2rem; border-radius: 20px; margin: 2rem 0; color: white; text-align: center;">
        <h2 style="margin: 0 0 1rem 0; font-size: 2rem; font-weight: 800;">🎮 Wildfire Safety Challenge</h2>
        <p style="font-size: 1.2rem; margin: 0;">Test your knowledge and learn life-saving wildfire safety tips!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'game_score' not in st.session_state:
        st.session_state.game_score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    
    # Quiz questions
    questions = [
        {
            "question": "How far should you clear vegetation from structures?",
            "options": ["10 feet", "20 feet", "30 feet", "50 feet"],
            "correct": 2,
            "explanation": "Create defensible space by clearing vegetation within 30 feet of structures."
        },
        {
            "question": "What should you do if trapped in a wildfire?",
            "options": ["Run uphill", "Find water or cleared area", "Hide in dense vegetation", "Drive through flames"],
            "correct": 1,
            "explanation": "Find the nearest body of water or cleared area and stay low to avoid smoke."
        },
        {
            "question": "Which plants are fire-resistant?",
            "options": ["Juniper and pine", "Lavender and rosemary", "Dry grass", "Dead branches"],
            "correct": 1,
            "explanation": "Fire-resistant plants like lavender and rosemary are safer landscaping choices."
        }
    ]
    
    if st.session_state.questions_answered < len(questions):
        current_q = questions[st.session_state.questions_answered]
        
        st.markdown(f"""
        <div style="background: white; padding: 2rem; border-radius: 16px; margin: 1rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
            <h3 style="color: {COLORS['primary']}; margin: 0 0 1rem 0;">Question {st.session_state.questions_answered + 1}</h3>
            <p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 1.5rem;">{current_q['question']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        for i, option in enumerate(current_q['options']):
            if st.button(f"{chr(65+i)}. {option}", key=f"option_{i}", use_container_width=True):
                if i == current_q['correct']:
                    st.session_state.game_score += 1
                    st.success(f"✅ Correct! {current_q['explanation']}")
                else:
                    st.error(f"❌ Incorrect. {current_q['explanation']}")
                
                st.session_state.questions_answered += 1
                time.sleep(2)
                st.rerun()
    else:
        # Show final score
        percentage = (st.session_state.game_score / len(questions)) * 100
        
        if percentage >= 80:
            badge = "🏆 Wildfire Safety Expert"
            color = "#28a745"
        elif percentage >= 60:
            badge = "🥉 Safety Aware"
            color = "#ffc107"
        else:
            badge = "📚 Keep Learning"
            color = "#dc3545"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color}, {color}dd); padding: 3rem; border-radius: 20px; text-align: center; color: white; margin: 2rem 0;">
            <h2 style="margin: 0 0 1rem 0;">{badge}</h2>
            <p style="font-size: 2rem; font-weight: 800; margin: 0 0 1rem 0;">Score: {st.session_state.game_score}/{len(questions)}</p>
            <p style="font-size: 1.2rem; margin: 0;">You got {percentage:.0f}% correct!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Play Again", use_container_width=True):
            st.session_state.game_score = 0
            st.session_state.questions_answered = 0
            st.rerun()

def create_flashcards(category, title):
    """Create interactive flashcards for educational content"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']}); padding: 2rem; border-radius: 20px; margin: 2rem 0; color: white; text-align: center;">
        <h3 style="margin: 0; font-size: 1.8rem; font-weight: 800;">{title}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    cards = EDUCATIONAL_CONTENT[category]
    
    
    # Create flashcard layout
    cols = st.columns(2)
    for i, card in enumerate(cards):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background: white; padding: 2rem; border-radius: 16px; margin: 1rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-left: 4px solid {COLORS['accent2']}; transition: transform 0.3s ease;">
                <div style="text-align: center; font-size: 3rem; margin-bottom: 1rem;">{card['icon']}</div>
                <h4 style="color: {COLORS['primary']}; margin: 0 0 0.5rem 0; font-weight: 700;">{card['title']}</h4>
                <p style="color: #4a5568; line-height: 1.6; margin: 0;">{card['content']}</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 2.5rem 1rem; background: linear-gradient(135deg, #dc2626 0%, #ea580c 50%, #d97706 100%); border-radius: 24px; margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(220, 38, 38, 0.4); position: relative; overflow: hidden;">
            <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); animation: rotate 20s linear infinite;"></div>
            <div style="position: relative; z-index: 1;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔥</div>
                <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 900; text-shadow: 2px 2px 8px rgba(0,0,0,0.4); letter-spacing: -1px;">WILDFIRE</h1>
                <h2 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.3rem; font-weight: 600; text-shadow: 1px 1px 4px rgba(0,0,0,0.3);">SAFETY HUB</h2>
                <div style="width: 60px; height: 3px; background: rgba(255,255,255,0.8); margin: 1rem auto 0; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <style>
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .sidebar-nav {
            background: linear-gradient(135deg, #ffffff 0%, #fef7ed 100%);
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(217, 119, 6, 0.15);
            border: 1px solid rgba(217, 119, 6, 0.1);
        }
        
        .sidebar-nav h3 {
            color: #dc2626;
            margin: 0 0 1rem 0;
            font-size: 1.1rem;
            font-weight: 700;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-nav"><h3>📍 Navigate</h3></div>', unsafe_allow_html=True)
        
        page = st.selectbox("", [
            "🚨 Emergency Reporting", 
            "📊 Statistics & Reports",
            "🔔 Notifications",
            "🎮 Safety Challenge", 
            "🌲 Forest Protection", 
            "🏃‍♂️ In Fire Zone", 
            "⚠️ Fire Nearby", 
            "🏥 Survivor Resources",
            "🚀 Future Improvements",
        ], label_visibility="collapsed")

        st.markdown("---")
        
        reports_df = get_wildfire_reports()
        if not reports_df.empty:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); padding: 2rem 1.5rem; border-radius: 20px; color: white; text-align: center; margin: 1rem 0; box-shadow: 0 12px 35px rgba(249, 115, 22, 0.4); position: relative; overflow: hidden;">
                <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.6;"></div>
                <div style="position: relative; z-index: 1;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: 900; text-shadow: 2px 2px 6px rgba(0,0,0,0.3);">{len(reports_df)}</h3>
                    <p style="margin: 0; font-size: 1rem; font-weight: 600; opacity: 0.95;">Active Reports</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            critical_count = len(reports_df[reports_df['severity'] == 'Critical'])
            if critical_count > 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); padding: 2rem 1.5rem; border-radius: 20px; color: white; text-align: center; margin: 1rem 0; box-shadow: 0 12px 35px rgba(220, 38, 38, 0.5); animation: pulse 3s infinite; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -15px; left: -15px; width: 60px; height: 60px; background: rgba(255,255,255,0.15); border-radius: 50%;"></div>
                    <div style="position: relative; z-index: 1;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚨</div>
                        <h3 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: 900; text-shadow: 2px 2px 6px rgba(0,0,0,0.4);">{critical_count}</h3>
                        <p style="margin: 0; font-size: 1rem; font-weight: 600;">Critical Alerts</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); padding: 2.5rem 1.5rem; border-radius: 24px; color: white; text-align: center; margin: 1rem 0; box-shadow: 0 15px 40px rgba(220, 38, 38, 0.5); position: relative; overflow: hidden; border: 2px solid rgba(255,255,255,0.2);">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);"></div>
            <div style="position: relative; z-index: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));">🚨</div>
                <h4 style="margin: 0 0 1rem 0; font-weight: 800; font-size: 1.3rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.4);">EMERGENCY</h4>
                <h2 style="margin: 0; font-size: 4rem; font-weight: 900; text-shadow: 3px 3px 10px rgba(0,0,0,0.5); letter-spacing: -2px;">911</h2>
                <p style="margin: 1rem 0 0 0; font-size: 1rem; opacity: 0.95; font-weight: 500;">Call immediately for emergencies</p>
                <div style="width: 80px; height: 3px; background: rgba(255,255,255,0.8); margin: 1rem auto 0; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    .main .block-container {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: none;
    }}
    
    .main {{
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #fef7ed 0%, #fed7aa 50%, #fdba74 100%);
        min-height: 100vh;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    
    /* Professional Info Cards */
    .info-card-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }}
    
    .info-card {{
        background: linear-gradient(135deg, white 0%, #fefbf7 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(217, 119, 6, 0.15);
        border: 1px solid rgba(217, 119, 6, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .info-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['accent2']});
    }}
    
    .info-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 60px rgba(217, 119, 6, 0.25);
    }}
    
    /* Enhanced Form Styling */
    .stForm {{
        background: white;
        padding: 3rem;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(217, 119, 6, 0.15);
        border: 1px solid rgba(217, 119, 6, 0.1);
        margin: 2rem 0;
    }}
    
    /* Button Enhancement */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['accent2']}, {COLORS['primary']});
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1.2rem 3rem;
        font-weight: 800;
        font-size: 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 30px rgba(220, 38, 38, 0.3);
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(220, 38, 38, 0.4);
        background: linear-gradient(135deg, #ef4444, {COLORS['accent2']});
    }}
    
    /* Map Container Enhancement */
    .map-container {{
        background: white;
        padding: 2rem;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(217, 119, 6, 0.15);
        margin: 2rem 0;
        border: 1px solid rgba(217, 119, 6, 0.1);
    }}
    
    /* Section Headers */
    .section-header {{
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['accent2']});
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 3rem 0 2rem 0;
        box-shadow: 0 10px 40px rgba(217, 119, 6, 0.3);
        text-align: center;
        position: relative;
        overflow: hidden;
    }}
    
    .section-header h2 {{
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        position: relative;
        z-index: 1;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    }}
    
    /* Input Styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {{
        border-radius: 12px;
        border: 2px solid #fed7aa;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }}
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {COLORS['primary']};
        box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.1);
        outline: none;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="position: relative; width: 100%; height: 400px; border-radius: 20px; overflow: hidden; margin-bottom: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.2);">
        <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-1lcMKcg8W3Ub1CNyJcfB6HHe3Vlc3e.png" style="width: 100%; height: 100%; object-fit: cover;">
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(217, 119, 6, 0.4)); display: flex; align-items: center; justify-content: center; text-align: center;">
            <div>
                <h1 style="color: white; margin: 0; font-size: 4rem; font-weight: 900; text-shadow: 3px 3px 10px rgba(0,0,0,0.7); font-family: 'Inter', sans-serif; letter-spacing: -2px;">🔥 WILDFIRE ALERT</h1>
                <p style="color: rgba(255,255,255,0.95); margin: 1.5rem 0 0 0; font-size: 1.6rem; font-weight: 500; text-shadow: 2px 2px 6px rgba(0,0,0,0.5); max-width: 800px;">Emergency Wildfire Reporting & Real-Time Monitoring System</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if page == "🚨 Emergency Reporting":
        reports_df = get_wildfire_reports()
        
        st.markdown("""
        <div class="info-card-container">
            <div class="info-card">
                <span class="info-card-icon">🚨</span>
                <h3 class="info-card-title">Emergency Reporting</h3>
                <p class="info-card-description">Report wildfires instantly with GPS location detection and real-time emergency response coordination.</p>
            </div>
            <div class="info-card">
                <span class="info-card-icon">🗺️</span>
                <h3 class="info-card-title">Live Tracking</h3>
                <p class="info-card-description">Monitor active wildfires on our interactive map with real-time updates and severity indicators.</p>
            </div>
            <div class="info-card">
                <span class="info-card-icon">🔔</span>
                <h3 class="info-card-title">Alert System</h3>
                <p class="info-card-description">Receive instant notifications about critical wildfire situations in your area.</p>
            </div>
            <div class="info-card">
                <p class="info-card-number">{}</p>
                <h3 class="info-card-title">Active Reports</h3>
                <p class="info-card-description">Total wildfire incidents currently being monitored by our system.</p>
            </div>
        </div>
        """.format(len(reports_df) if not reports_df.empty else 0), unsafe_allow_html=True)

        col1, col2 = st.columns([1.2, 1.8], gap="large")
        
        with col1:
            st.markdown('<div class="section-header"><h2>🚨 Report Emergency</h2></div>', unsafe_allow_html=True)
            
            components.html(get_user_location(), height=250)

            with st.form("wildfire_report"):
                st.markdown('<div class="form-section"><h3>👤 Reporter Information</h3></div>', unsafe_allow_html=True)
                reporter_name = st.text_input("Full Name*", placeholder="Enter your full name")
                
                col_email, col_phone = st.columns(2)
                with col_email:
                    reporter_email = st.text_input("Email Address", placeholder="your.email@example.com")
                with col_phone:
                    reporter_phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
                
                st.markdown('<div class="form-section"><h3>📍 Location Information</h3></div>', unsafe_allow_html=True)
                
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    latitude = st.number_input("Latitude*", value=0.0, format="%.6f")
                with col_lon:
                    longitude = st.number_input("Longitude*", value=0.0, format="%.6f")
                
                location_desc = st.text_input("Location Description*", placeholder="e.g., Highway 101, 2 miles north of Pine Valley")
                
                st.markdown('<div class="form-section"><h3>🔥 Fire Information</h3></div>', unsafe_allow_html=True)
                col_size, col_severity = st.columns(2)
                with col_size:
                    fire_size = st.selectbox("Estimated Fire Size", [
                        "Small (< 1 acre)", 
                        "Medium (1-10 acres)", 
                        "Large (10-100 acres)", 
                        "Massive (> 100 acres)"
                    ])
                with col_severity:
                    severity = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"])
                
                description = st.text_area("Detailed Description*", 
                    placeholder="Describe what you observe: smoke color, flame height, wind direction, weather conditions, nearby structures at risk, etc.", 
                    height=120)
                
                submitted = st.form_submit_button("🚨 SUBMIT EMERGENCY REPORT")
                
                if submitted:
                    if reporter_name and latitude != 0.0 and longitude != 0.0 and location_desc and description:
                        report_data = (
                            reporter_name, reporter_email, reporter_phone,
                            latitude, longitude, location_desc,
                            fire_size, severity, description
                        )
                        
                        if create_wildfire_report(report_data):
                            st.success("✅ Emergency report submitted! Authorities have been notified.")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Failed to submit report. Please try again.")
                    else:
                        st.error("⚠️ Please fill in all required fields marked with *")

        with col2:
            st.markdown('<div class="section-header"><h2>🗺️ Live Wildfire Map</h2></div>', unsafe_allow_html=True)
            
            if not reports_df.empty:
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Total Reports", len(reports_df), delta=None)
                with col_stat2:
                    critical_count = len(reports_df[reports_df['severity'] == 'Critical'])
                    st.metric("Critical", critical_count, delta=None)
                with col_stat3:
                    active_count = len(reports_df[reports_df['status'] == 'Active'])
                    st.metric("Active", active_count, delta=None)
                with col_stat4:
                    verified_count = len(reports_df[reports_df['verified'] == 1])
                    st.metric("Verified", verified_count, delta=None)
                
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                wildfire_map = create_map(reports_df)
                st_folium(wildfire_map, width=None, height=800)
                st.markdown("</div>", unsafe_allow_html=True)
                
            else:
                st.info("📍 No wildfire reports available. Be the first to report!")
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                default_map = create_map(pd.DataFrame())
                st_folium(default_map, width=None, height=800)
                st.markdown("</div>", unsafe_allow_html=True)

    elif page == "📊 Statistics & Reports":
        st.markdown('<div class="section-header"><h2>📊 Wildfire Statistics & Reports</h2></div>', unsafe_allow_html=True)
        
        reports_df = get_wildfire_reports()
        if not reports_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Reports", len(reports_df))
            with col2:
                critical_count = len(reports_df[reports_df['severity'] == 'Critical'])
                st.metric("Critical Fires", critical_count)
            with col3:
                active_count = len(reports_df[reports_df['status'] == 'Active'])
                st.metric("Active Fires", active_count)
            with col4:
                verified_count = len(reports_df[reports_df['verified'] == 1])
                st.metric("Verified Reports", verified_count)
            
            st.markdown("### 📋 Recent Reports")
            st.dataframe(reports_df[['reporter_name', 'location_description', 'severity', 'fire_size', 'status', 'reported_at']], use_container_width=True)
        else:
            st.info("No reports available yet.")

    elif page == "🔔 Notifications":
        st.markdown('<div class="section-header"><h2>🔔 Emergency Notifications</h2></div>', unsafe_allow_html=True)
        
        notifications_df = get_notifications()
        if not notifications_df.empty:
            for _, notification in notifications_df.iterrows():
                alert_color = COLORS['accent2'] if notification['notification_type'] == 'Alert' else COLORS['primary']
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 16px; margin: 1rem 0; box-shadow: 0 8px 25px rgba(217, 119, 6, 0.1); border-left: 4px solid {alert_color};">
                    <h4 style="color: {alert_color}; margin: 0 0 0.5rem 0;">{notification['notification_type']}</h4>
                    <p style="margin: 0 0 0.5rem 0; font-weight: 600;">{notification['message']}</p>
                    <p style="margin: 0; color: #78716c; font-size: 0.9rem;">📍 {notification['location_description']} • {notification['created_at']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No notifications available.")

    elif page == "🎮 Safety Challenge":
        create_flashcard_game()
        
    elif page == "🌲 Forest Protection":
        create_flashcards("forest_protection", "🌲 Actions to Protect Forests & Mitigate Wildfires")
        
    elif page == "🏃‍♂️ In Fire Zone":
        create_flashcards("wildfire_location", "🏃‍♂️ How to Protect Yourself When IN a Wildfire")
        
    elif page == "⚠️ Fire Nearby":
        create_flashcards("fire_nearby", "⚠️ How to Protect Yourself When Fire is Nearby")
        
    elif page == "🏥 Survivor Resources":
        create_flashcards("survivor_locations", "🏥 Locations That Provide Necessities for Survivors")
    elif page == "🚀 Future Improvements":
        st.markdown('<div class="section-header"><h2>🚀 Future Improvements</h2></div>', unsafe_allow_html=True)
        create_flashcards("future_improvements", "🚀 Planned Features & Enhancements")
        st.markdown("### 💬 Share Your Feedback & Suggestions Below")

if __name__ == "__main__":
    main()
