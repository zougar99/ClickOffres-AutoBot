from __future__ import annotations

import asyncio
import json
import os
import random
import threading
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import customtkinter as ctk
from tkinter import filedialog, messagebox

from form_engine import AnalysisResult, DEVICE_PROFILES, FIELD_PATTERNS, FormEngine, ProxyConfig
from profile_studio import ProfileStudioStore
from proxy_center import ProxyCheckResult, export_proxy_results_csv, normalize_proxy_entries, parse_proxy_line, pick_best_proxy
from ui_theme import THEME

DATA_FILE = Path(__file__).parent / "user_data.json"
PROXY_FILE = Path(__file__).parent / "proxy_config.json"
PROXY_LIST_FILE = Path(__file__).parent / "proxy_list.json"
PROFILES_FILE = Path(__file__).parent / "profiles.json"
TEMPLATES_FILE = Path(__file__).parent / "templates.json"
REPORTS_FILE = Path(__file__).parent / "run_history.json"
SESSIONS_DIR = Path(__file__).parent / "sessions"
COUNTRY_PRESETS_FILE = Path(__file__).parent / "fake_data" / "COUNTRY_PRESETS.json"

DEFAULT_SETTINGS = {"device_profile": "Windows", "selected_devices": ["Windows"], "fill_mode": "random"}
DEFAULT_DATA = {
    "first_name": "", "last_name": "", "full_name": "", "email": "", "phone": "",
    "address": "", "city": "", "zip_code": "", "country": "Morocco", "company": "",
    "job_title": "", "website": "", "linkedin": "", "username": "", "password": "",
    "date_of_birth": "", "gender": "", "message": "", "cv_upload": "",
}
DEFAULT_TEMPLATES = {
    "Developer Basic": {
        "settings": {"device_profile": "Windows", "fill_mode": "sequential"},
        "user_data": {"job_title": "Software Engineer || Backend Developer"},
    }
}

FAKE_DATA_DIR = Path(__file__).parent / "fake_data"
FAKE_LIST_FILES = {
    "first_names": "FIRST_NAMES.TXT",
    "last_names": "LAST_NAMES.TXT",
    "cities": "CITIES.TXT",
    "countries": "COUNTRIES.TXT",
    "companies": "COMPANIES.TXT",
    "job_titles": "JOB_TITLES.TXT",
    "genders": "GENDERS.TXT",
    "messages": "MESSAGES.TXT",
    "street_names": "STREET_NAMES.TXT",
    "email_domains": "EMAIL_DOMAINS.TXT",
    "website_domains": "WEBSITE_DOMAINS.TXT",
    "linkedin_prefixes": "LINKEDIN_PREFIXES.TXT",
    "phone_prefixes": "PHONE_PREFIXES.TXT",
    "zip_prefixes": "ZIP_PREFIXES.TXT",
    "birth_years": "BIRTH_YEARS.TXT",
    "password_prefixes": "PASSWORD_PREFIXES.TXT",
}
FAKE_DEFAULTS = {
    "first_names": ["Adam", "Noah", "Lina", "Sara", "Yassine", "Omar", "Maya", "Rania"],
    "last_names": ["Martin", "Benali", "Lopez", "Haddad", "Amrani", "Karim", "Safi", "Nadir"],
    "cities": ["Casablanca", "Rabat", "Marrakesh", "Tangier", "Agadir", "Fes"],
    "countries": ["Morocco"],
    "companies": ["Atlas Solutions", "Nova Systems", "BlueBridge", "Zenith Labs", "Pixel Forge"],
    "job_titles": ["QA Tester", "Support Agent", "Junior Developer", "Data Assistant", "Operations Analyst"],
    "genders": ["Male", "Female"],
    "messages": ["Hello, this is a generated fake profile used for legal QA testing only."],
    "street_names": ["Test Avenue", "Demo Street", "Sample Boulevard", "QA Lane"],
    "email_domains": ["example.test"],
    "website_domains": ["example.test"],
    "linkedin_prefixes": ["https://linkedin.com/in"],
    "phone_prefixes": ["+2126"],
    "zip_prefixes": ["10", "20", "30", "40", "50"],
    "birth_years": ["1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004"],
    "password_prefixes": ["Test", "Demo", "QA", "Legal", "Sample"],
}
COUNTRY_FAKE_PRESETS = {
    "morocco": {
        "cities": ["Casablanca", "Rabat", "Marrakesh", "Tangier", "Agadir", "Fes"],
        "phone_prefixes": ["+2126", "+2127", "+2125"],
        "zip_prefixes": ["10", "20", "30", "40", "50"],
        "street_names": ["Avenue Hassan", "Rue Atlas", "Boulevard Mohammed", "Rue Palmier"],
    },
    "france": {
        "cities": ["Paris", "Lyon", "Marseille", "Lille", "Toulouse", "Nantes"],
        "phone_prefixes": ["+336", "+337"],
        "zip_prefixes": ["75", "69", "13", "59", "31"],
        "street_names": ["Rue Victor Hugo", "Avenue Republique", "Rue de Paris", "Boulevard Voltaire"],
    },
    "spain": {
        "cities": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
        "phone_prefixes": ["+346", "+347"],
        "zip_prefixes": ["28", "08", "46", "41", "48"],
        "street_names": ["Calle Mayor", "Avenida Sol", "Calle Gran Via", "Calle Luna"],
    },
    "portugal": {
        "cities": ["Lisbon", "Porto", "Braga", "Coimbra", "Faro"],
        "phone_prefixes": ["+3519"],
        "zip_prefixes": ["10", "40", "47", "30", "80"],
        "street_names": ["Rua Central", "Avenida Atlantico", "Rua Nova", "Rua Jardim"],
    },
    "algeria": {
        "cities": ["Algiers", "Oran", "Constantine", "Annaba", "Blida"],
        "phone_prefixes": ["+2135", "+2136", "+2137"],
        "zip_prefixes": ["16", "31", "25", "23", "09"],
        "street_names": ["Rue Emir", "Avenue Alger", "Rue Oasis", "Boulevard Cedres"],
    },
    "tunisia": {
        "cities": ["Tunis", "Sfax", "Sousse", "Gabes", "Bizerte"],
        "phone_prefixes": ["+2162", "+2165", "+2169"],
        "zip_prefixes": ["10", "30", "40", "60", "70"],
        "street_names": ["Rue Carthage", "Avenue Habib", "Rue Jasmin", "Boulevard Medina"],
    },
    "egypt": {
        "cities": ["Cairo", "Alexandria", "Giza", "Mansoura", "Aswan"],
        "phone_prefixes": ["+2010", "+2011", "+2012", "+2015"],
        "zip_prefixes": ["11", "21", "12", "35", "81"],
        "street_names": ["Nile Street", "Tahrir Avenue", "Palm Road", "Lotus Street"],
    },
    "saudiarabia": {
        "cities": ["Riyadh", "Jeddah", "Dammam", "Mecca", "Medina"],
        "phone_prefixes": ["+9665"],
        "zip_prefixes": ["11", "21", "31", "24", "42"],
        "street_names": ["King Road", "Falcon Street", "Oasis Avenue", "Desert Boulevard"],
    },
    "unitedarabemirates": {
        "cities": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Al Ain"],
        "phone_prefixes": ["+97150", "+97152", "+97154", "+97155", "+97156", "+97158"],
        "zip_prefixes": ["00", "10", "20", "30", "40"],
        "street_names": ["Sheikh Zayed Road", "Marina Street", "Palm Avenue", "Creek Boulevard"],
    },
    "qatar": {
        "cities": ["Doha", "Al Rayyan", "Al Wakrah", "Lusail", "Umm Salal"],
        "phone_prefixes": ["+9743", "+9745", "+9746", "+9747"],
        "zip_prefixes": ["10", "20", "30", "40", "50"],
        "street_names": ["Pearl Street", "Corniche Avenue", "Falcon Road", "Souq Boulevard"],
    },
    "kuwait": {
        "cities": ["Kuwait City", "Hawalli", "Farwaniya", "Ahmadi", "Jahra"],
        "phone_prefixes": ["+9655", "+9656", "+9659"],
        "zip_prefixes": ["10", "20", "30", "40", "50"],
        "street_names": ["Gulf Road", "Salmiya Street", "Sabah Avenue", "Desert Street"],
    },
    "bahrain": {
        "cities": ["Manama", "Riffa", "Muharraq", "Hamad Town", "Isa Town"],
        "phone_prefixes": ["+9733", "+9736"],
        "zip_prefixes": ["10", "20", "30", "40", "50"],
        "street_names": ["Pearl Road", "Kingdom Avenue", "Harbor Street", "Date Palm Road"],
    },
    "oman": {
        "cities": ["Muscat", "Salalah", "Sohar", "Nizwa", "Sur"],
        "phone_prefixes": ["+9687", "+9689"],
        "zip_prefixes": ["10", "20", "30", "40", "50"],
        "street_names": ["Sultan Road", "Wadi Street", "Frankincense Avenue", "Coast Boulevard"],
    },
    "jordan": {
        "cities": ["Amman", "Zarqa", "Irbid", "Aqaba", "Madaba"],
        "phone_prefixes": ["+9627"],
        "zip_prefixes": ["11", "13", "21", "31", "17"],
        "street_names": ["Rainbow Street", "Petra Avenue", "Jordan Road", "Desert Lane"],
    },
    "turkey": {
        "cities": ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya"],
        "phone_prefixes": ["+9050", "+9053", "+9054", "+9055"],
        "zip_prefixes": ["34", "06", "35", "16", "07"],
        "street_names": ["Ataturk Caddesi", "Bosphorus Road", "Istanbul Sokak", "Anatolia Avenue"],
    },
    "germany": {
        "cities": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
        "phone_prefixes": ["+4915", "+4916", "+4917"],
        "zip_prefixes": ["10", "80", "20", "60", "50"],
        "street_names": ["Hauptstrasse", "Bahnhofstrasse", "Lindenweg", "Berliner Allee"],
    },
    "italy": {
        "cities": ["Rome", "Milan", "Naples", "Turin", "Bologna"],
        "phone_prefixes": ["+3931", "+3932", "+3933", "+3934", "+3935"],
        "zip_prefixes": ["00", "20", "80", "10", "40"],
        "street_names": ["Via Roma", "Via Milano", "Corso Italia", "Via Garibaldi"],
    },
    "netherlands": {
        "cities": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
        "phone_prefixes": ["+316"],
        "zip_prefixes": ["10", "30", "25", "35", "56"],
        "street_names": ["Damstraat", "Kanaalweg", "Oranje Laan", "Tulip Avenue"],
    },
    "belgium": {
        "cities": ["Brussels", "Antwerp", "Ghent", "Liege", "Bruges"],
        "phone_prefixes": ["+324", "+3246", "+3247", "+3248", "+3249"],
        "zip_prefixes": ["10", "20", "90", "40", "80"],
        "street_names": ["Rue Royale", "Avenue Louise", "Korenmarkt", "Canal Road"],
    },
    "switzerland": {
        "cities": ["Zurich", "Geneva", "Basel", "Lausanne", "Bern"],
        "phone_prefixes": ["+4176", "+4177", "+4178", "+4179"],
        "zip_prefixes": ["80", "12", "40", "10", "30"],
        "street_names": ["Bahnhofstrasse", "Rue du Lac", "Alpine Road", "Helvetia Avenue"],
    },
    "austria": {
        "cities": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck"],
        "phone_prefixes": ["+4366", "+4367", "+4368"],
        "zip_prefixes": ["10", "80", "40", "50", "60"],
        "street_names": ["Ringstrasse", "Mozartgasse", "Alpenweg", "Donau Strasse"],
    },
    "sweden": {
        "cities": ["Stockholm", "Gothenburg", "Malmo", "Uppsala", "Vasteras"],
        "phone_prefixes": ["+4670", "+4672", "+4673", "+4676"],
        "zip_prefixes": ["11", "40", "20", "75", "72"],
        "street_names": ["Kungsgatan", "Nordic Avenue", "Lake Road", "Birch Street"],
    },
    "norway": {
        "cities": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Tromso"],
        "phone_prefixes": ["+474", "+479"],
        "zip_prefixes": ["01", "50", "70", "40", "90"],
        "street_names": ["Fjord Road", "Nordlys Avenue", "Harbor Street", "Mountain Lane"],
    },
    "denmark": {
        "cities": ["Copenhagen", "Aarhus", "Odense", "Aalborg", "Esbjerg"],
        "phone_prefixes": ["+452", "+453", "+454", "+455", "+456", "+457", "+458", "+459"],
        "zip_prefixes": ["10", "80", "50", "90", "67"],
        "street_names": ["Nyhavn Street", "Harbor Avenue", "Viking Road", "Bridge Lane"],
    },
    "poland": {
        "cities": ["Warsaw", "Krakow", "Wroclaw", "Gdansk", "Poznan"],
        "phone_prefixes": ["+4850", "+4851", "+4853", "+4857", "+4860"],
        "zip_prefixes": ["00", "30", "50", "80", "60"],
        "street_names": ["Ulica Krolewska", "Solidarity Avenue", "Vistula Road", "Market Street"],
    },
    "romania": {
        "cities": ["Bucharest", "Cluj-Napoca", "Timisoara", "Iasi", "Constanta"],
        "phone_prefixes": ["+4072", "+4073", "+4074", "+4075", "+4076", "+4077", "+4078"],
        "zip_prefixes": ["01", "40", "30", "70", "90"],
        "street_names": ["Bulevard Unirii", "Carpathian Street", "Danube Road", "Liberty Avenue"],
    },
    "greece": {
        "cities": ["Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa"],
        "phone_prefixes": ["+3069"],
        "zip_prefixes": ["10", "54", "26", "71", "41"],
        "street_names": ["Acropolis Street", "Aegean Avenue", "Olive Road", "Marina Lane"],
    },
    "ireland": {
        "cities": ["Dublin", "Cork", "Galway", "Limerick", "Waterford"],
        "phone_prefixes": ["+3538"],
        "zip_prefixes": ["D0", "T1", "H9", "V9", "X9"],
        "street_names": ["Shamrock Road", "River Liffey Street", "Celtic Avenue", "Green Lane"],
    },
    "unitedkingdom": {
        "cities": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
        "phone_prefixes": ["+4474", "+4475", "+4477", "+4478", "+4479"],
        "zip_prefixes": ["EC", "M", "B", "LS", "G"],
        "street_names": ["King Street", "Baker Street", "Oxford Road", "Queen Avenue"],
    },
    "canada": {
        "cities": ["Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa"],
        "phone_prefixes": ["+1514", "+1416", "+1604", "+1403", "+1613"],
        "zip_prefixes": ["M", "H", "V", "T", "K"],
        "street_names": ["Maple Street", "Lakeshore Road", "Pine Avenue", "River Road"],
    },
    "unitedstates": {
        "cities": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
        "phone_prefixes": ["+1212", "+1310", "+1312", "+1713", "+1305"],
        "zip_prefixes": ["10", "90", "60", "77", "33"],
        "street_names": ["Main Street", "Sunset Boulevard", "Liberty Avenue", "Oak Road"],
    },
    "mexico": {
        "cities": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana"],
        "phone_prefixes": ["+5255", "+5233", "+5281", "+5222", "+52664"],
        "zip_prefixes": ["01", "44", "64", "72", "22"],
        "street_names": ["Avenida Reforma", "Calle Hidalgo", "Calle Juarez", "Plaza Road"],
    },
    "brazil": {
        "cities": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Curitiba"],
        "phone_prefixes": ["+5511", "+5521", "+5561", "+5571", "+5541"],
        "zip_prefixes": ["01", "20", "70", "40", "80"],
        "street_names": ["Avenida Paulista", "Rua Central", "Praia Avenue", "Samba Street"],
    },
    "argentina": {
        "cities": ["Buenos Aires", "Cordoba", "Rosario", "Mendoza", "La Plata"],
        "phone_prefixes": ["+54911", "+549351", "+549341", "+549261", "+549221"],
        "zip_prefixes": ["10", "50", "20", "55", "19"],
        "street_names": ["Avenida Libertador", "Calle San Martin", "Pampa Road", "Rio Street"],
    },
    "chile": {
        "cities": ["Santiago", "Valparaiso", "Concepcion", "Antofagasta", "La Serena"],
        "phone_prefixes": ["+569"],
        "zip_prefixes": ["83", "23", "40", "12", "17"],
        "street_names": ["Andes Avenue", "Pacific Street", "Vina Road", "Central Boulevard"],
    },
    "colombia": {
        "cities": ["Bogota", "Medellin", "Cali", "Barranquilla", "Cartagena"],
        "phone_prefixes": ["+5730", "+5731", "+5732", "+5735"],
        "zip_prefixes": ["11", "05", "76", "08", "13"],
        "street_names": ["Calle 80", "Avenida Colombia", "Andina Road", "Plaza Street"],
    },
    "india": {
        "cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"],
        "phone_prefixes": ["+9190", "+9191", "+9192", "+9193", "+9194", "+9195", "+9196", "+9197", "+9198", "+9199"],
        "zip_prefixes": ["40", "11", "56", "50", "60"],
        "street_names": ["MG Road", "Nehru Avenue", "Lotus Street", "Tech Park Road"],
    },
    "pakistan": {
        "cities": ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad"],
        "phone_prefixes": ["+9230", "+9231", "+9232", "+9233", "+9234"],
        "zip_prefixes": ["74", "54", "44", "46", "38"],
        "street_names": ["Jinnah Road", "Iqbal Avenue", "Garden Street", "Central Lane"],
    },
    "bangladesh": {
        "cities": ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet"],
        "phone_prefixes": ["+88017", "+88018", "+88019", "+88016", "+88015"],
        "zip_prefixes": ["12", "40", "90", "60", "31"],
        "street_names": ["Victory Road", "Padma Street", "Delta Avenue", "Bengal Lane"],
    },
    "indonesia": {
        "cities": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang"],
        "phone_prefixes": ["+6281", "+6282", "+6283", "+6285", "+6287", "+6288", "+6289"],
        "zip_prefixes": ["10", "60", "40", "20", "50"],
        "street_names": ["Jalan Merdeka", "Jalan Sudirman", "Nusantara Avenue", "Lotus Road"],
    },
    "malaysia": {
        "cities": ["Kuala Lumpur", "Johor Bahru", "Penang", "Ipoh", "Kota Kinabalu"],
        "phone_prefixes": ["+6010", "+6011", "+6012", "+6013", "+6014", "+6016", "+6017", "+6018", "+6019"],
        "zip_prefixes": ["50", "80", "10", "30", "88"],
        "street_names": ["Jalan Bukit", "Jalan Merdeka", "Harbor Avenue", "Palm Street"],
    },
    "singapore": {
        "cities": ["Singapore", "Jurong", "Woodlands", "Tampines", "Pasir Ris"],
        "phone_prefixes": ["+658", "+659"],
        "zip_prefixes": ["01", "60", "73", "52", "51"],
        "street_names": ["Orchard Road", "Marina Boulevard", "Lion City Street", "Bayfront Avenue"],
    },
    "thailand": {
        "cities": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Khon Kaen"],
        "phone_prefixes": ["+669"],
        "zip_prefixes": ["10", "50", "83", "20", "40"],
        "street_names": ["Sukhumvit Road", "Rama Avenue", "Lotus Road", "Golden Street"],
    },
    "vietnam": {
        "cities": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong", "Can Tho"],
        "phone_prefixes": ["+8490", "+8491", "+8492", "+8493", "+8494", "+8496", "+8497", "+8498"],
        "zip_prefixes": ["10", "70", "55", "18", "90"],
        "street_names": ["Nguyen Hue Street", "Lotus Avenue", "Dragon Road", "Old Quarter Lane"],
    },
    "china": {
        "cities": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu"],
        "phone_prefixes": ["+8613", "+8615", "+8617", "+8618", "+8619"],
        "zip_prefixes": ["10", "20", "51", "51", "61"],
        "street_names": ["Chang An Avenue", "Pearl Road", "Dragon Street", "Lotus Boulevard"],
    },
    "japan": {
        "cities": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo"],
        "phone_prefixes": ["+8180", "+8190", "+8170"],
        "zip_prefixes": ["10", "53", "22", "45", "06"],
        "street_names": ["Sakura Street", "Shibuya Avenue", "Harbor Road", "Fuji Lane"],
    },
    "southkorea": {
        "cities": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],
        "phone_prefixes": ["+8210"],
        "zip_prefixes": ["03", "47", "21", "41", "34"],
        "street_names": ["Han River Road", "Sejong Avenue", "Ginkgo Street", "City Hall Lane"],
    },
    "australia": {
        "cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
        "phone_prefixes": ["+614"],
        "zip_prefixes": ["20", "30", "40", "60", "50"],
        "street_names": ["Eucalyptus Road", "Harbor Street", "Kangaroo Avenue", "Coral Lane"],
    },
    "newzealand": {
        "cities": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Dunedin"],
        "phone_prefixes": ["+6420", "+6421", "+6422", "+6427", "+6429"],
        "zip_prefixes": ["10", "60", "80", "32", "90"],
        "street_names": ["Kiwi Road", "Harbor Avenue", "Fern Street", "Southern Lane"],
    },
    "southafrica": {
        "cities": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth"],
        "phone_prefixes": ["+2771", "+2772", "+2773", "+2774", "+2776", "+2778", "+2779"],
        "zip_prefixes": ["20", "80", "40", "00", "60"],
        "street_names": ["Nelson Avenue", "Table Mountain Road", "Savanna Street", "Cape Boulevard"],
    },
    "nigeria": {
        "cities": ["Lagos", "Abuja", "Kano", "Port Harcourt", "Ibadan"],
        "phone_prefixes": ["+23470", "+23480", "+23481", "+23490", "+23491"],
        "zip_prefixes": ["10", "90", "70", "50", "20"],
        "street_names": ["Unity Road", "Lagos Avenue", "Niger Street", "Palm Grove Road"],
    },
    "kenya": {
        "cities": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
        "phone_prefixes": ["+2547", "+2541"],
        "zip_prefixes": ["00", "80", "40", "20", "30"],
        "street_names": ["Uhuru Street", "Safari Avenue", "Savanna Road", "Lake Street"],
    },
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ClickOffres AutoBot")
        self.geometry("1400x860")
        self.minsize(1180, 740)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=THEME.bg_main)

        self.engine = FormEngine()
        self.analysis_result: AnalysisResult | None = None
        self.sequential_indices: dict[str, int] = {}
        self.proxy_check_results: list[ProxyCheckResult] = []
        self.run_history = self._load_json(REPORTS_FILE, [])

        self.loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._async_thread.start()

        self.user_data = self._load_json(DATA_FILE, DEFAULT_DATA)
        self.proxy_config = ProxyConfig.from_dict(self._load_json(PROXY_FILE, {}))
        proxy_bundle = self._load_json(PROXY_LIST_FILE, {"items": [], "saved_working": []})
        self.proxy_list = [str(x).strip() for x in proxy_bundle.get("items", []) if str(x).strip()]
        self.saved_working_proxies = [str(x).strip() for x in proxy_bundle.get("saved_working", []) if str(x).strip()]

        self.store = ProfileStudioStore(
            profiles_file=PROFILES_FILE,
            templates_file=TEMPLATES_FILE,
            default_data=DEFAULT_DATA,
            default_settings=DEFAULT_SETTINGS,
            default_templates=DEFAULT_TEMPLATES,
        )
        self.profiles = self.store.load_profiles(self.user_data, self.proxy_config)
        self.templates = self.store.load_templates()
        self.current_profile_name = "default" if "default" in self.profiles else next(iter(self.profiles.keys()))
        self.fake_lists = self._load_fake_lists()
        self.country_presets = self._load_country_presets()
        self.smart_run_cancel_requested = False
        self.smart_run_paused = False
        self.last_smart_run_details: list[str] = []
        self.report_callback_exception = self._handle_tk_exception

        self._build_ui()
        self._apply_profile(self.current_profile_name)
        self._refresh_reports()
        self._show_panel("general")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _handle_tk_exception(self, exc_type, exc_value, exc_tb):
        err_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            self._set_status("UI action failed. See error dialog.", THEME.danger)
            self._append_report("ui_exception", "error", str(exc_value))
        except Exception:
            pass
        try:
            messagebox.showerror("Application Error", err_text[-4000:])
        except Exception:
            pass

    def _run_async(self, coro, callback):
        async def wrapper():
            try:
                res = await coro
                self.after(0, callback, res, None)
            except Exception as e:
                self.after(0, callback, None, e)
        asyncio.run_coroutine_threadsafe(wrapper(), self.loop)

    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(default, dict) and isinstance(data, dict):
                    return {**default, **data}
                return data
            except Exception:
                pass
        return default.copy() if isinstance(default, dict) else list(default) if isinstance(default, list) else default

    def _save_json(self, path: Path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_text_list(self, path: Path, fallback: list[str]) -> list[str]:
        if path.exists():
            try:
                lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
                values = [line for line in lines if line and not line.startswith("#")]
                if values:
                    return values
            except Exception:
                pass
        return fallback[:]

    def _load_fake_lists(self) -> dict[str, list[str]]:
        FAKE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        out: dict[str, list[str]] = {}
        for key, file_name in FAKE_LIST_FILES.items():
            path = FAKE_DATA_DIR / file_name
            out[key] = self._read_text_list(path, FAKE_DEFAULTS.get(key, []))
        return out

    def _load_country_presets(self) -> dict:
        COUNTRY_PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if COUNTRY_PRESETS_FILE.exists():
            try:
                data = json.loads(COUNTRY_PRESETS_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data:
                    return data
            except Exception:
                pass
        # First run: export built-in presets so user can edit from file.
        try:
            COUNTRY_PRESETS_FILE.write_text(
                json.dumps(COUNTRY_FAKE_PRESETS, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        return COUNTRY_FAKE_PRESETS.copy()

    def _append_report(self, event: str, status: str, details: str):
        self.run_history.append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": event, "status": status, "details": details})
        self._save_json(REPORTS_FILE, self.run_history[-300:])
        self._refresh_reports()
        self._refresh_dashboard_stats()

    def _refresh_dashboard_stats(self):
        if hasattr(self, "stat_profiles_label"):
            self.stat_profiles_label.configure(text=f"Profiles\n{len(self.profiles)}")
        if hasattr(self, "stat_proxies_label"):
            self.stat_proxies_label.configure(text=f"Working Proxies\n{len(self.saved_working_proxies)}")
        if hasattr(self, "stat_runs_label"):
            self.stat_runs_label.configure(text=f"Recent Runs\n{len(self.run_history[-50:])}")

    def _set_status(self, txt: str, color: str = THEME.text_muted):
        self.status_label.configure(text=txt, text_color=color)

    def _log(self, txt: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", txt + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _normalize_url(self, raw: str) -> str:
        x = raw.strip()
        if not x:
            return ""
        if x.startswith(("http://", "https://")):
            return x
        return "https://" + x

    def _parse_list_values(self, raw: str) -> list[str]:
        return [x.strip() for x in raw.replace("\r\n", "\n").replace("\r", "\n").replace("||", "\n").split("\n") if x.strip()]

    def _collect_data(self) -> dict:
        data = {}
        for k, w in self.data_entries.items():
            data[k] = w.get("1.0", "end-1c") if isinstance(w, ctk.CTkTextbox) else w.get()
        return data

    def _get_data_value(self, key: str) -> str:
        w = self.data_entries.get(key)
        if not w:
            return ""
        return w.get("1.0", "end-1c") if isinstance(w, ctk.CTkTextbox) else w.get()

    def _collect_proxy(self) -> ProxyConfig:
        return ProxyConfig(
            enabled=self.proxy_enabled_var.get(),
            server=self.proxy_server_entry.get().strip(),
            username=self.proxy_user_entry.get().strip(),
            password=self.proxy_pass_entry.get().strip(),
        )

    def _set_selected_devices(self, devices: list[str] | None):
        valid = [d for d in (devices or []) if d in DEVICE_PROFILES]
        if not valid:
            valid = [self.device_profile_var.get() if self.device_profile_var.get() in DEVICE_PROFILES else "Windows"]
        for name, var in self.device_multi_vars.items():
            var.set(name in valid)
        self.device_profile_var.set(valid[0])

    def _get_selected_devices(self) -> list[str]:
        selected = [name for name, var in self.device_multi_vars.items() if var.get()]
        if selected:
            return selected
        fallback = self.device_profile_var.get()
        if fallback not in DEVICE_PROFILES:
            fallback = "Windows"
        self._set_selected_devices([fallback])
        return [fallback]

    def _on_device_checks_changed(self):
        selected = self._get_selected_devices()
        if selected:
            self.device_profile_var.set(selected[0])

    def _save_runtime(self):
        self.user_data = self._collect_data()
        self.proxy_config = self._collect_proxy()
        self.proxy_list = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        self._save_json(DATA_FILE, self.user_data)
        self._save_json(PROXY_FILE, self.proxy_config.to_dict())
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=230)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self, fg_color=THEME.bg_sidebar, corner_radius=0, border_width=1, border_color=THEME.border)
        side.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(
            side,
            text="ClickOffres\nAutoBot",
            font=ctk.CTkFont(size=22, weight="bold"),
            justify="left",
            text_color=THEME.text_primary,
        ).pack(anchor="w", padx=14, pady=(16, 10))
        ctk.CTkLabel(
            side,
            text="Profile and run manager",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=14, pady=(0, 10))
        self.nav_buttons = {}
        for key in ["general", "proxy", "platform", "session", "reports", "logs"]:
            btn = ctk.CTkButton(
                side,
                text=key.capitalize(),
                fg_color=THEME.bg_panel,
                hover_color=THEME.accent_hover,
                text_color=THEME.text_primary,
                command=lambda k=key: self._show_panel(k),
                height=38,
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[key] = btn
        ctk.CTkLabel(
            side,
            text="Legal QA/testing only",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=11),
        ).pack(side="bottom", anchor="w", padx=12, pady=(0, 2))
        ctk.CTkLabel(
            side,
            text="Telegram: werlist99",
            text_color=THEME.accent,
            font=ctk.CTkFont(size=11, underline=True),
        ).pack(side="bottom", anchor="w", padx=12, pady=(0, 12))

        main = ctk.CTkFrame(self, fg_color=THEME.bg_main, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(main, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border)
        top.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            top,
            text="Target URL",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")
        self.url_entry = ctk.CTkEntry(top, placeholder_text="https://example.com/apply", fg_color=THEME.bg_panel)
        self.url_entry.grid(row=0, column=1, padx=10, pady=(10, 6), sticky="ew")
        ctk.CTkLabel(
            top,
            text="Login URL",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        self.login_url_entry = ctk.CTkEntry(top, placeholder_text="https://example.com/login", fg_color=THEME.bg_panel)
        self.login_url_entry.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        stats.grid_columnconfigure(0, weight=1)
        stats.grid_columnconfigure(1, weight=1)
        stats.grid_columnconfigure(2, weight=1)

        self.stat_profiles_label = ctk.CTkLabel(
            ctk.CTkFrame(stats, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border),
            text=f"Profiles\n{len(self.profiles)}",
            justify="left",
            text_color=THEME.text_primary,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.stat_profiles_label.master.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.stat_profiles_label.pack(anchor="w", padx=12, pady=10)

        self.stat_proxies_label = ctk.CTkLabel(
            ctk.CTkFrame(stats, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border),
            text=f"Working Proxies\n{len(self.saved_working_proxies)}",
            justify="left",
            text_color=THEME.text_primary,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.stat_proxies_label.master.grid(row=0, column=1, sticky="ew", padx=3)
        self.stat_proxies_label.pack(anchor="w", padx=12, pady=10)

        self.stat_runs_label = ctk.CTkLabel(
            ctk.CTkFrame(stats, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border),
            text=f"Recent Runs\n{len(self.run_history[-50:])}",
            justify="left",
            text_color=THEME.text_primary,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.stat_runs_label.master.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        self.stat_runs_label.pack(anchor="w", padx=12, pady=10)

        self.host = ctk.CTkFrame(main, fg_color=THEME.bg_main, corner_radius=0)
        self.host.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.host.grid_rowconfigure(0, weight=1)
        self.host.grid_columnconfigure(0, weight=1)

        self.panels = {
            "general": self._panel_general(self.host),
            "proxy": self._panel_proxy(self.host),
            "platform": self._panel_platform(self.host),
            "session": self._panel_session(self.host),
            "reports": self._panel_reports(self.host),
            "logs": self._panel_logs(self.host),
        }
        for p in self.panels.values():
            p.grid(row=0, column=0, sticky="nsew")

        self.status_label = ctk.CTkLabel(main, text="Ready", text_color=THEME.text_muted, anchor="w")
        self.status_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 4))
        self.progress = ctk.CTkProgressBar(main)
        self.progress.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.progress.set(0)

    def _panel_general(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        p.grid_rowconfigure(2, weight=1)
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        self.profile_name_entry = ctk.CTkEntry(row, width=180, placeholder_text="Profile name")
        self.profile_name_entry.pack(side="left", padx=(0, 6))
        self.profile_selector_var = ctk.StringVar(value=self.current_profile_name)
        self.profile_selector = ctk.CTkOptionMenu(row, variable=self.profile_selector_var, values=["default"], width=180)
        self.profile_selector.pack(side="left", padx=6)
        ctk.CTkButton(row, text="Save", command=self._on_save_profile).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Load", command=self._on_load_profile).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Delete", fg_color=THEME.danger, hover_color="#991b1b", command=self._on_delete_profile).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Save Data", command=self._on_save_data).pack(side="left", padx=8)
        row2 = ctk.CTkFrame(p, fg_color="transparent")
        row2.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.template_selector_var = ctk.StringVar(value="Developer Basic")
        self.template_selector = ctk.CTkOptionMenu(row2, variable=self.template_selector_var, values=["Developer Basic"], width=180)
        self.template_selector.pack(side="left", padx=(0, 6))
        ctk.CTkButton(row2, text="Apply Template", command=self._on_apply_template).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Save as Template", command=self._on_save_template).pack(side="left", padx=4)
        self.fake_country_var = ctk.StringVar(value="Auto (country field)")
        country_choices = ["Auto (country field)"] + sorted(self.fake_lists.get("countries", []))
        self.fake_country_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.fake_country_var,
            values=country_choices,
            width=190,
            command=self._on_fake_country_selected,
        )
        self.fake_country_menu.pack(side="left", padx=6)
        ctk.CTkButton(row2, text="Generate Fake Data", command=self._on_generate_fake_data).pack(side="left", padx=8)
        ctk.CTkButton(row2, text="Bulk Fake Profiles", command=self._on_bulk_generate_fake_profiles).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Open fake_data", command=lambda: os.startfile(str(FAKE_DATA_DIR))).pack(side="left", padx=6)
        ctk.CTkButton(row2, text="Open Country Presets", command=lambda: os.startfile(str(COUNTRY_PRESETS_FILE))).pack(side="left", padx=4)
        data = ctk.CTkScrollableFrame(p, fg_color=THEME.bg_card)
        data.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.data_entries = {}
        for k in DEFAULT_DATA:
            ctk.CTkLabel(data, text=k, text_color=THEME.text_muted).pack(anchor="w", padx=6, pady=(6, 2))
            if k == "message":
                w = ctk.CTkTextbox(data, height=80)
            else:
                w = ctk.CTkEntry(data)
            w.pack(fill="x", padx=6)
            self.data_entries[k] = w
        return p

    def _panel_proxy(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        p.grid_rowconfigure(3, weight=1)
        p.grid_columnconfigure(0, weight=1)

        # KPI strip (Dolphin-style quick proxy stats)
        kpi_card = ctk.CTkFrame(p, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border)
        kpi_card.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        kpi_card.grid_columnconfigure(0, weight=1)
        kpi_card.grid_columnconfigure(1, weight=1)
        kpi_card.grid_columnconfigure(2, weight=1)
        kpi_card.grid_columnconfigure(3, weight=1)
        self.proxy_kpi_total = ctk.CTkLabel(kpi_card, text="Input\n0", justify="left", font=ctk.CTkFont(size=13, weight="bold"))
        self.proxy_kpi_total.grid(row=0, column=0, sticky="w", padx=12, pady=8)
        self.proxy_kpi_checked = ctk.CTkLabel(kpi_card, text="Checked\n0", justify="left", font=ctk.CTkFont(size=13, weight="bold"))
        self.proxy_kpi_checked.grid(row=0, column=1, sticky="w", padx=12, pady=8)
        self.proxy_kpi_ok = ctk.CTkLabel(kpi_card, text="Working\n0", justify="left", text_color=THEME.success, font=ctk.CTkFont(size=13, weight="bold"))
        self.proxy_kpi_ok.grid(row=0, column=2, sticky="w", padx=12, pady=8)
        self.proxy_kpi_active = ctk.CTkLabel(
            kpi_card,
            text="Active Proxy\nNone",
            justify="left",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.proxy_kpi_active.grid(row=0, column=3, sticky="w", padx=12, pady=8)

        # Runtime configuration block
        runtime_card = ctk.CTkFrame(p, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border)
        runtime_card.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        runtime_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(runtime_card, text="Runtime Proxy", text_color=THEME.text_muted).grid(
            row=0, column=0, padx=10, pady=(8, 4), sticky="w"
        )
        self.proxy_enabled_var = ctk.BooleanVar(value=self.proxy_config.enabled)
        ctk.CTkSwitch(runtime_card, text="Enable", variable=self.proxy_enabled_var, command=self._on_proxy_toggle).grid(
            row=0, column=1, padx=10, pady=(8, 4), sticky="w"
        )

        self.proxy_server_entry = ctk.CTkEntry(runtime_card, placeholder_text="http://host:port")
        self.proxy_server_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=4)

        auth_row = ctk.CTkFrame(runtime_card, fg_color="transparent")
        auth_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 8))
        self.proxy_user_entry = ctk.CTkEntry(auth_row, width=180, placeholder_text="username")
        self.proxy_user_entry.pack(side="left", padx=(0, 6))
        self.proxy_pass_entry = ctk.CTkEntry(auth_row, width=180, placeholder_text="password", show="*")
        self.proxy_pass_entry.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(auth_row, text="Max proxies").pack(side="left", padx=(0, 4))
        self.max_proxies_entry = ctk.CTkEntry(auth_row, width=80, placeholder_text="0=all")
        self.max_proxies_entry.pack(side="left", padx=(0, 10))
        self.max_proxies_entry.insert(0, "0")
        ctk.CTkLabel(auth_row, text="Timeout (s)").pack(side="left", padx=(0, 4))
        self.proxy_timeout_var = ctk.IntVar(value=12)
        self.proxy_timeout_slider = ctk.CTkSlider(auth_row, from_=6, to=30, number_of_steps=24, width=150)
        self.proxy_timeout_slider.set(12)
        self.proxy_timeout_slider.pack(side="left", padx=4)
        self.proxy_timeout_label = ctk.CTkLabel(auth_row, text="12")
        self.proxy_timeout_label.pack(side="left", padx=(2, 0))
        self.proxy_timeout_slider.configure(command=lambda v: self.proxy_timeout_label.configure(text=str(int(v))))
        ctk.CTkLabel(auth_row, text="Check profile").pack(side="left", padx=(12, 4))
        ctk.CTkButton(auth_row, text="Fast", width=58, command=lambda: self._set_proxy_check_profile("fast")).pack(side="left", padx=2)
        ctk.CTkButton(auth_row, text="Balanced", width=86, command=lambda: self._set_proxy_check_profile("balanced")).pack(side="left", padx=2)
        ctk.CTkButton(auth_row, text="Deep", width=58, command=lambda: self._set_proxy_check_profile("deep")).pack(side="left", padx=2)

        # Actions block
        actions_card = ctk.CTkFrame(p, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border)
        actions_card.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        actions_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_row.pack(fill="x", padx=10, pady=8)
        ctk.CTkButton(actions_row, text="Save List", command=self._on_save_proxy_list).pack(side="left", padx=(0, 6))
        self.check_proxy_btn = ctk.CTkButton(actions_row, text="Check", command=self._on_check_proxies)
        self.check_proxy_btn.pack(side="left", padx=6)
        ctk.CTkButton(actions_row, text="Remove Unsupported", command=self._on_remove_unsupported_proxies).pack(side="left", padx=6)
        ctk.CTkButton(actions_row, text="Use Best", command=self._on_use_best_proxy).pack(side="left", padx=6)
        ctk.CTkButton(actions_row, text="Export CSV", command=self._on_export_proxy_results).pack(side="left", padx=6)

        self.saved_proxy_var = ctk.StringVar(value="")
        self.saved_proxy_menu = ctk.CTkOptionMenu(actions_row, variable=self.saved_proxy_var, values=[""], width=220)
        self.saved_proxy_menu.pack(side="left", padx=8)
        ctk.CTkButton(actions_row, text="Apply Saved", command=self._on_apply_saved_proxy).pack(side="left")
        self.proxy_country_filter_var = ctk.StringVar(value="All countries")
        self.proxy_country_filter_menu = ctk.CTkOptionMenu(
            actions_row,
            variable=self.proxy_country_filter_var,
            values=["All countries"],
            width=170,
        )
        self.proxy_country_filter_menu.pack(side="left", padx=8)
        self.proxy_deep_check_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(actions_row, text="Deep Check", variable=self.proxy_deep_check_var).pack(side="left", padx=6)
        ctk.CTkButton(actions_row, text="Keep Country", command=self._on_keep_country_proxies).pack(side="left", padx=4)

        self.proxy_summary_label = ctk.CTkLabel(
            actions_card,
            text="Total: 0 | OK: 0 | FAIL: 0",
            text_color=THEME.text_muted,
            anchor="w",
            justify="left",
        )
        self.proxy_summary_label.pack(fill="x", padx=12, pady=(0, 8))

        # List/results block
        body_card = ctk.CTkFrame(p, fg_color=THEME.bg_card, border_width=1, border_color=THEME.border)
        body_card.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        body_card.grid_columnconfigure(0, weight=1)
        body_card.grid_columnconfigure(1, weight=1)
        body_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(body_card, text="Proxy Pool", text_color=THEME.text_muted).grid(
            row=0, column=0, sticky="w", padx=(10, 6), pady=(8, 2)
        )
        ctk.CTkLabel(body_card, text="Checker Results", text_color=THEME.text_muted).grid(
            row=0, column=1, sticky="w", padx=(6, 10), pady=(8, 2)
        )
        self.proxy_list_box = ctk.CTkTextbox(body_card)
        self.proxy_list_box.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(0, 10))
        self.proxy_results_box = ctk.CTkTextbox(body_card)
        self.proxy_results_box.grid(row=1, column=1, sticky="nsew", padx=(6, 10), pady=(0, 10))
        self.proxy_results_box.configure(state="disabled")
        self.proxy_country_breakdown_box = ctk.CTkTextbox(body_card, height=92)
        self.proxy_country_breakdown_box.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.proxy_country_breakdown_box.insert("1.0", "Country breakdown will appear here.")
        self.proxy_country_breakdown_box.configure(state="disabled")
        self._refresh_proxy_kpis()
        return p

    def _panel_platform(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        p.grid_rowconfigure(1, weight=1)
        t = ctk.CTkFrame(p, fg_color=THEME.bg_card)
        t.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        t.grid_columnconfigure(0, weight=1)

        # Row 1: device and run behavior settings
        cfg_row = ctk.CTkFrame(t, fg_color="transparent")
        cfg_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        self.device_profile_var = ctk.StringVar(value="Windows")
        self.fill_mode_var = ctk.StringVar(value="random")
        ctk.CTkLabel(cfg_row, text="Primary").pack(side="left", padx=(0, 2), pady=4)
        ctk.CTkOptionMenu(
            cfg_row,
            variable=self.device_profile_var,
            values=list(DEVICE_PROFILES.keys()),
            width=120,
        ).pack(side="left", padx=(0, 10), pady=4)
        ctk.CTkLabel(cfg_row, text="Multi-device").pack(side="left", padx=(2, 4), pady=4)
        self.device_multi_vars = {}
        for name in DEVICE_PROFILES.keys():
            var = ctk.BooleanVar(value=(name == "Windows"))
            self.device_multi_vars[name] = var
            ctk.CTkCheckBox(cfg_row, text=name, variable=var, command=self._on_device_checks_changed).pack(side="left", padx=3, pady=4)
        ctk.CTkLabel(cfg_row, text="Fill Mode").pack(side="left", padx=(8, 4), pady=4)
        ctk.CTkOptionMenu(cfg_row, variable=self.fill_mode_var, values=["random", "sequential"], width=120).pack(side="left", padx=4, pady=4)
        self.auto_submit_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cfg_row, text="Auto Submit", variable=self.auto_submit_var).pack(side="left", padx=8, pady=4)
        self.smart_assist_clicks_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cfg_row, text="Smart Assist Clicks", variable=self.smart_assist_clicks_var).pack(side="left", padx=8, pady=4)
        self.smart_ai_flow_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cfg_row, text="AI Flow", variable=self.smart_ai_flow_var).pack(side="left", padx=8, pady=4)
        self.safe_mode_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cfg_row, text="Safe Mode", variable=self.safe_mode_var).pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(cfg_row, text="Delay between browsers (s)").pack(side="left", padx=(8, 4), pady=4)
        self.browser_delay_entry = ctk.CTkEntry(cfg_row, width=70, placeholder_text="0")
        self.browser_delay_entry.pack(side="left", padx=(0, 4), pady=4)
        self.browser_delay_entry.insert(0, "30")
        ctk.CTkButton(cfg_row, text="10s", width=48, command=lambda: self._set_browser_delay(10)).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(cfg_row, text="25s", width=48, command=lambda: self._set_browser_delay(25)).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(cfg_row, text="30s", width=48, command=lambda: self._set_browser_delay(30)).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(cfg_row, text="35s", width=48, command=lambda: self._set_browser_delay(35)).pack(side="left", padx=2, pady=4)

        # Row 2: core run controls
        run_row = ctk.CTkFrame(t, fg_color="transparent")
        run_row.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        self.smart_run_btn = ctk.CTkButton(run_row, text="Smart Run", command=self._on_smart_run)
        self.smart_run_btn.pack(side="left", padx=4, pady=4)
        self.stop_smart_run_btn = ctk.CTkButton(
            run_row,
            text="Stop",
            fg_color=THEME.danger,
            hover_color="#991b1b",
            state="disabled",
            command=self._on_stop_smart_run,
        )
        self.stop_smart_run_btn.pack(side="left", padx=4, pady=4)
        self.pause_smart_run_btn = ctk.CTkButton(
            run_row,
            text="Pause",
            state="disabled",
            command=self._on_pause_resume_smart_run,
        )
        self.pause_smart_run_btn.pack(side="left", padx=4, pady=4)
        self.analyze_btn = ctk.CTkButton(run_row, text="Analyze", command=self._on_analyze)
        self.analyze_btn.pack(side="left", padx=4, pady=4)
        self.preview_btn = ctk.CTkButton(run_row, text="Preview", state="disabled", command=self._on_preview_fill)
        self.preview_btn.pack(side="left", padx=4, pady=4)
        self.fill_btn = ctk.CTkButton(run_row, text="Fill", state="disabled", command=self._on_fill)
        self.fill_btn.pack(side="left", padx=4, pady=4)
        self.submit_btn = ctk.CTkButton(run_row, text="Submit", state="disabled", command=self._on_submit)
        self.submit_btn.pack(side="left", padx=4, pady=4)

        # Row 3: utilities and AI helpers
        tools_row = ctk.CTkFrame(t, fg_color="transparent")
        tools_row.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))
        ctk.CTkLabel(tools_row, text="Utilities", text_color=THEME.text_muted).pack(side="left", padx=(4, 6), pady=4)
        self.platform_tools_var = ctk.StringVar(value="Tools")
        self.platform_tools_menu = ctk.CTkOptionMenu(
            tools_row,
            variable=self.platform_tools_var,
            values=[
                "Tools",
                "Run Details",
                "Reload Fake Lists",
                "Health Check",
                "Quick Run",
                "AI Auto Map",
                "AI Suggest Data",
                "Export Profiles",
                "Import Profiles",
                "Clear All Fields",
                "Reset Sequential Indices",
                "Open Sessions Folder",
                "Export Profiles CSV",
                "About",
            ],
            width=220,
            command=self._on_platform_tool_menu,
        )
        self.platform_tools_menu.pack(side="left", padx=4, pady=4)
        ctk.CTkButton(tools_row, text="Quick Run", command=self._on_quick_run).pack(side="left", padx=6, pady=4)

        self.mapping_scroll = ctk.CTkScrollableFrame(p, fg_color=THEME.bg_card)
        self.mapping_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        return p

    def _panel_session(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        b = ctk.CTkFrame(p, fg_color=THEME.bg_card)
        b.pack(fill="x", padx=10, pady=10)
        self.login_btn = ctk.CTkButton(b, text="Open Login Session", command=self._on_open_login_session)
        self.login_btn.pack(side="left", padx=8, pady=8)
        ctk.CTkButton(b, text="Save Session", command=self._on_save_session).pack(side="left", padx=6)
        ctk.CTkButton(b, text="Load Session", command=self._on_load_session).pack(side="left", padx=6)
        return p

    def _panel_reports(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        p.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(p, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        ctk.CTkButton(top, text="Export JSON", command=self._on_export_reports).pack(side="right")
        ctk.CTkButton(top, text="Clear Reports", command=self._on_clear_reports).pack(side="right", padx=6)
        self.reports_box = ctk.CTkTextbox(p)
        self.reports_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        return p

    def _panel_logs(self, parent):
        p = ctk.CTkFrame(parent, fg_color=THEME.bg_panel)
        p.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(p, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        ctk.CTkButton(top, text="Clear Logs", command=self._on_clear_logs).pack(side="right")
        self.log_box = ctk.CTkTextbox(p)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_box.configure(state="disabled")
        return p

    def _show_panel(self, key: str):
        for panel_key, panel in self.panels.items():
            if panel_key == key:
                panel.tkraise()
                self.nav_buttons[panel_key].configure(fg_color=THEME.accent)
            else:
                self.nav_buttons[panel_key].configure(fg_color=THEME.bg_panel)

    # Actions
    def _on_save_data(self):
        self._sync_profile()
        self._save_runtime()
        self._append_report("save_data", "ok", self.current_profile_name)
        self._set_status("Saved", THEME.success)

    def _sync_profile(self):
        self.current_profile_name = self.profile_name_entry.get().strip() or self.current_profile_name
        data = self._collect_data()
        proxy = self._collect_proxy()
        self.profiles[self.current_profile_name] = {
            "user_data": data,
            "proxy": proxy.to_dict(),
            "settings": {
                "device_profile": self.device_profile_var.get(),
                "selected_devices": self._get_selected_devices(),
                "fill_mode": self.fill_mode_var.get(),
            },
        }
        self.store.save_profiles(self.profiles)
        self._refresh_profile_menu()

    def _refresh_profile_menu(self):
        names = sorted(self.profiles.keys())
        self.profile_selector.configure(values=names or ["default"])
        if names:
            self.profile_selector_var.set(self.current_profile_name if self.current_profile_name in names else names[0])
        self._refresh_dashboard_stats()

    def _refresh_template_menu(self):
        names = sorted(self.templates.keys())
        self.template_selector.configure(values=names or ["Developer Basic"])
        if names:
            cur = self.template_selector_var.get()
            self.template_selector_var.set(cur if cur in names else names[0])

    def _refresh_saved_proxy_menu(self):
        values = self.saved_working_proxies[:] or [""]
        self.saved_proxy_menu.configure(values=values)
        self.saved_proxy_var.set(values[0] if values else "")
        self._refresh_dashboard_stats()

    def _apply_profile(self, name: str):
        p = self.profiles.get(name)
        if not p:
            return
        self.current_profile_name = name
        self.profile_name_entry.delete(0, "end")
        self.profile_name_entry.insert(0, name)
        data = {**DEFAULT_DATA, **p.get("user_data", {})}
        for k, w in self.data_entries.items():
            v = data.get(k, "")
            if isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
                if v:
                    w.insert("1.0", v)
            else:
                w.delete(0, "end")
                if v:
                    w.insert(0, v)
        if hasattr(self, "fake_country_var"):
            country_value = str(data.get("country", "")).strip()
            options = ["Auto (country field)"] + sorted(self.fake_lists.get("countries", []))
            self.fake_country_menu.configure(values=options)
            self.fake_country_var.set(country_value if country_value in options else "Auto (country field)")
        proxy = ProxyConfig.from_dict(p.get("proxy", {}))
        self.proxy_enabled_var.set(proxy.enabled)
        self.proxy_server_entry.delete(0, "end")
        self.proxy_server_entry.insert(0, proxy.server)
        self.proxy_user_entry.delete(0, "end")
        self.proxy_user_entry.insert(0, proxy.username)
        self.proxy_pass_entry.delete(0, "end")
        self.proxy_pass_entry.insert(0, proxy.password)
        s = {**DEFAULT_SETTINGS, **p.get("settings", {})}
        self.device_profile_var.set(s["device_profile"] if s["device_profile"] in DEVICE_PROFILES else "Windows")
        selected_devices = s.get("selected_devices", [self.device_profile_var.get()])
        self._set_selected_devices(selected_devices if isinstance(selected_devices, list) else [self.device_profile_var.get()])
        self.fill_mode_var.set(s["fill_mode"] if s["fill_mode"] in ("random", "sequential") else "random")
        self._refresh_profile_menu()
        self._refresh_template_menu()
        self._refresh_saved_proxy_menu()
        self.proxy_list_box.delete("1.0", "end")
        if self.proxy_list:
            self.proxy_list_box.insert("1.0", "\n".join(self.proxy_list))
        self._refresh_proxy_kpis()

    def _on_save_profile(self):
        if not self.profile_name_entry.get().strip():
            messagebox.showwarning("Profile name required", "Enter profile name first.")
            return
        self._on_save_data()

    def _on_load_profile(self):
        n = self.profile_selector_var.get().strip()
        if n in self.profiles:
            self._apply_profile(n)
            self._append_report("load_profile", "ok", n)

    def _on_delete_profile(self):
        n = self.profile_selector_var.get().strip()
        if n not in self.profiles or len(self.profiles) <= 1:
            return
        if messagebox.askyesno("Delete profile", f"Delete profile '{n}'?"):
            del self.profiles[n]
            self.store.save_profiles(self.profiles)
            self._apply_profile(sorted(self.profiles.keys())[0])
            self._append_report("delete_profile", "ok", n)

    def _on_apply_template(self):
        t = self.templates.get(self.template_selector_var.get().strip())
        if not t:
            return
        for k, v in t.get("user_data", {}).items():
            w = self.data_entries.get(k)
            if not w:
                continue
            if isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
                w.insert("1.0", v)
            else:
                w.delete(0, "end")
                w.insert(0, v)
        s = {**DEFAULT_SETTINGS, **t.get("settings", {})}
        self.device_profile_var.set(s["device_profile"] if s["device_profile"] in DEVICE_PROFILES else "Windows")
        selected_devices = s.get("selected_devices", [self.device_profile_var.get()])
        self._set_selected_devices(selected_devices if isinstance(selected_devices, list) else [self.device_profile_var.get()])
        self.fill_mode_var.set(s["fill_mode"] if s["fill_mode"] in ("random", "sequential") else "random")

    def _on_save_template(self):
        name = self.profile_name_entry.get().strip() or self.current_profile_name
        if not name:
            return
        self.templates[name] = {
            "settings": {
                "device_profile": self.device_profile_var.get(),
                "selected_devices": self._get_selected_devices(),
                "fill_mode": self.fill_mode_var.get(),
            },
            "user_data": self._collect_data(),
        }
        self.store.save_templates(self.templates)
        self._refresh_template_menu()
        self.template_selector_var.set(name)

    def _build_fake_profile_data(self, preferred_countries: list[str] | None = None) -> dict:
        first = self._pick_fake("first_names")
        last = self._pick_fake("last_names")
        full = f"{first} {last}"
        slug = f"{first}.{last}".lower().replace(" ", "")
        num = random.randint(100, 9999)
        city = self._pick_fake("cities")
        country_choices = preferred_countries or self.fake_lists.get("countries") or FAKE_DEFAULTS["countries"]
        country = random.choice(country_choices)
        country_profile = self._get_country_fake_profile(country) or {}
        company = self._pick_fake("companies")
        job = self._pick_fake("job_titles")
        street_values = country_profile.get("street_names") or (self.fake_lists.get("street_names") or FAKE_DEFAULTS["street_names"])
        street_name = random.choice(street_values)
        email_domain = self._pick_fake("email_domains")
        website_domain = self._pick_fake("website_domains")
        linkedin_prefix = self._pick_fake("linkedin_prefixes").rstrip("/")
        phone_values = country_profile.get("phone_prefixes") or (self.fake_lists.get("phone_prefixes") or FAKE_DEFAULTS["phone_prefixes"])
        zip_values = country_profile.get("zip_prefixes") or (self.fake_lists.get("zip_prefixes") or FAKE_DEFAULTS["zip_prefixes"])
        city_values = country_profile.get("cities") or (self.fake_lists.get("cities") or FAKE_DEFAULTS["cities"])
        phone_prefix = random.choice(phone_values)
        zip_prefix = random.choice(zip_values)
        city = random.choice(city_values)
        password_prefix = self._pick_fake("password_prefixes")
        gender = self._pick_fake("genders")
        message = self._pick_fake("messages")
        try:
            year = int(self._pick_fake("birth_years"))
        except Exception:
            year = random.randint(1990, 2004)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        return {
            "first_name": first,
            "last_name": last,
            "full_name": full,
            "email": f"{slug}{num}@{email_domain}",
            "phone": f"{phone_prefix}{random.randint(10000000, 99999999)}",
            "address": f"{random.randint(1, 400)} {street_name}",
            "city": city,
            "zip_code": f"{zip_prefix}{random.randint(1000, 9999)}",
            "country": country,
            "company": company,
            "job_title": job,
            "website": f"https://{slug}{num}.{website_domain}",
            "linkedin": f"{linkedin_prefix}/{slug}-{num}",
            "username": f"{slug}{num}",
            "password": f"{password_prefix}_{random.randint(10,99)}{first[:2]}!{random.randint(100,999)}",
            "date_of_birth": f"{year:04d}-{month:02d}-{day:02d}",
            "gender": gender,
            "message": message,
            "cv_upload": "",
        }

    def _pick_fake(self, key: str) -> str:
        values = self.fake_lists.get(key) or FAKE_DEFAULTS.get(key) or [""]
        return random.choice(values)

    def _normalize_country_key(self, country: str) -> str:
        cleaned = "".join(ch.lower() for ch in country if ch.isalnum())
        aliases = {
            "usa": "unitedstates",
            "us": "unitedstates",
            "uk": "unitedkingdom",
        }
        return aliases.get(cleaned, cleaned)

    def _get_country_fake_profile(self, country: str) -> dict | None:
        key = self._normalize_country_key(country)
        preset = self.country_presets.get(key) if isinstance(self.country_presets, dict) else None
        if not preset:
            preset = COUNTRY_FAKE_PRESETS.get(key)
        if preset:
            return preset
        if key in ("unitedstates", "unitedkingdom", "germany", "italy", "netherlands", "belgium"):
            # Lightweight fallback presets for common countries.
            return {
                "cities": self.fake_lists.get("cities") or FAKE_DEFAULTS["cities"],
                "phone_prefixes": self.fake_lists.get("phone_prefixes") or FAKE_DEFAULTS["phone_prefixes"],
                "zip_prefixes": self.fake_lists.get("zip_prefixes") or FAKE_DEFAULTS["zip_prefixes"],
                "street_names": self.fake_lists.get("street_names") or FAKE_DEFAULTS["street_names"],
            }
        return None

    def _on_fake_country_selected(self, country_value: str):
        if country_value == "Auto (country field)":
            return
        country_entry = self.data_entries.get("country")
        if country_entry and not isinstance(country_entry, ctk.CTkTextbox):
            country_entry.delete(0, "end")
            country_entry.insert(0, country_value)
        # One-click country to generate matching fake data.
        self._on_generate_fake_data()

    def _apply_data_to_form(self, data: dict):
        for k, w in self.data_entries.items():
            v = data.get(k, "")
            if isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
                if v:
                    w.insert("1.0", v)
            else:
                w.delete(0, "end")
                if v:
                    w.insert(0, v)

    def _on_generate_fake_data(self):
        selected_country = self.fake_country_var.get().strip() if hasattr(self, "fake_country_var") else ""
        if selected_country and selected_country != "Auto (country field)":
            country_values = [selected_country]
        else:
            country_values = self._parse_list_values(self._get_data_value("country"))
        fake = self._build_fake_profile_data(preferred_countries=country_values or None)
        self._apply_data_to_form(fake)
        self._sync_profile()
        self._save_runtime()
        self._set_status("Generated fake data for current profile", THEME.success)
        self._append_report("generate_fake_data", "ok", self.current_profile_name)

    def _on_bulk_generate_fake_profiles(self):
        count_text = ctk.CTkInputDialog(
            title="Bulk Fake Profiles",
            text="How many fake profiles do you want to generate? (1-200)",
        ).get_input()
        if not count_text:
            return
        try:
            count = int(count_text.strip())
            count = max(1, min(count, 200))
        except Exception:
            messagebox.showwarning("Invalid number", "Please enter a valid number between 1 and 200.")
            return

        created = []
        selected_country = self.fake_country_var.get().strip() if hasattr(self, "fake_country_var") else ""
        if selected_country and selected_country != "Auto (country field)":
            country_values = [selected_country]
        else:
            country_values = self._parse_list_values(self._get_data_value("country"))
        for _ in range(count):
            fake = self._build_fake_profile_data(preferred_countries=country_values or None)
            profile_name = f"fake_{fake['username']}"
            self.profiles[profile_name] = {
                "user_data": fake,
                "proxy": self._collect_proxy().to_dict(),
                "settings": {"device_profile": self.device_profile_var.get(), "fill_mode": self.fill_mode_var.get()},
            }
            created.append(profile_name)

        self.store.save_profiles(self.profiles)
        self._refresh_profile_menu()
        if created:
            self._apply_profile(created[-1])
        self._set_status(f"Created {len(created)} fake profiles", THEME.success)
        self._append_report("bulk_fake_profiles", "ok", f"count={len(created)}")

    def _on_export_profiles(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self._save_json(Path(path), self.profiles)

    def _on_import_profiles(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        data = self._load_json(Path(path), {})
        if isinstance(data, dict) and data:
            self.profiles.update(data)
            self.store.save_profiles(self.profiles)
            self._apply_profile(sorted(self.profiles.keys())[0])

    def _on_proxy_toggle(self):
        st = "normal" if self.proxy_enabled_var.get() else "disabled"
        self.proxy_server_entry.configure(state=st)
        self.proxy_user_entry.configure(state=st)
        self.proxy_pass_entry.configure(state=st)
        self._refresh_proxy_kpis()

    def _set_proxy_check_profile(self, mode: str):
        if mode == "fast":
            self.proxy_deep_check_var.set(False)
            self.proxy_timeout_slider.set(8)
            self.proxy_timeout_label.configure(text="8")
            self._set_status("Proxy profile: Fast (quick scan)", THEME.text_muted)
            return
        if mode == "deep":
            self.proxy_deep_check_var.set(True)
            self.proxy_timeout_slider.set(20)
            self.proxy_timeout_label.configure(text="20")
            self._set_status("Proxy profile: Deep (strict validation)", THEME.text_muted)
            return
        self.proxy_deep_check_var.set(False)
        self.proxy_timeout_slider.set(12)
        self.proxy_timeout_label.configure(text="12")
        self._set_status("Proxy profile: Balanced", THEME.text_muted)

    def _refresh_proxy_kpis(self):
        if not hasattr(self, "proxy_kpi_total"):
            return
        total_input = len(normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))) if hasattr(self, "proxy_list_box") else len(self.proxy_list)
        checked = len(self.proxy_check_results)
        ok_count = len([r for r in self.proxy_check_results if r.ok])
        active_proxy = self.proxy_server_entry.get().strip() if hasattr(self, "proxy_server_entry") else ""
        active_proxy_text = active_proxy if active_proxy else "None"
        if len(active_proxy_text) > 28:
            active_proxy_text = active_proxy_text[:25] + "..."
        self.proxy_kpi_total.configure(text=f"Input\n{total_input}")
        self.proxy_kpi_checked.configure(text=f"Checked\n{checked}")
        self.proxy_kpi_ok.configure(text=f"Working\n{ok_count}")
        self.proxy_kpi_active.configure(text=f"Active Proxy\n{active_proxy_text}")

    def _on_save_proxy_list(self):
        self.proxy_list = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})
        self._refresh_proxy_kpis()

    def _get_proxy_timeout_ms(self) -> int:
        try:
            seconds = int(float(self.proxy_timeout_slider.get()))
            return max(6, min(30, seconds)) * 1000
        except Exception:
            return 12000

    def _get_max_proxies_to_check(self, total_entries: int) -> int:
        try:
            raw = self.max_proxies_entry.get().strip()
            if not raw:
                return total_entries
            v = int(raw)
            if v <= 0:
                return total_entries
            return min(v, total_entries)
        except Exception:
            return total_entries

    def _get_browser_delay_seconds(self) -> int:
        try:
            raw = self.browser_delay_entry.get().strip()
            if not raw:
                return 0
            v = int(raw)
            return max(0, min(v, 120))
        except Exception:
            return 0

    def _set_browser_delay(self, seconds: int):
        self.browser_delay_entry.delete(0, "end")
        self.browser_delay_entry.insert(0, str(max(0, min(int(seconds), 120))))

    async def _wait_if_paused(self):
        while self.smart_run_paused and not self.smart_run_cancel_requested:
            await asyncio.sleep(0.25)

    async def _sleep_interruptible(self, seconds: int):
        end_time = asyncio.get_running_loop().time() + max(0, seconds)
        while asyncio.get_running_loop().time() < end_time:
            if self.smart_run_cancel_requested:
                return
            await self._wait_if_paused()
            await asyncio.sleep(0.25)

    async def _tcp_connectable(self, server_url: str, timeout_ms: int = 2000) -> bool:
        try:
            parsed = urlparse(server_url)
            host = parsed.hostname
            port = parsed.port
            if not host or not port:
                return False
            conn = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=timeout_ms / 1000)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _probe_proxy_candidate(
        self, i: int, raw: str, base_timeout: int, retry_timeout: int, deep_check: bool = False
    ) -> ProxyCheckResult:
        item = raw.strip()
        if item.lower().startswith("socks4://"):
            return ProxyCheckResult(
                i, raw, raw, False, 0, "", "", "Unsupported in Chromium: use http/https/socks5"
            )
        cfg = parse_proxy_line(item)
        if not cfg or not cfg.is_valid:
            return ProxyCheckResult(i, raw, raw, False, 0, "", "", "Invalid format")

        # Quick fail for dead ports before expensive HTTP probing.
        tcp_ok = await self._tcp_connectable(cfg.server, timeout_ms=min(2500, base_timeout))
        if not tcp_ok:
            return ProxyCheckResult(i, raw, cfg.server, False, 0, "", "", "TCP connect failed (host/port unreachable)")

        probe = await FormEngine.probe_proxy(cfg, timeout_ms=base_timeout, fast_mode=not deep_check)
        if not bool(probe.get("ok")):
            retry_probe = await FormEngine.probe_proxy(cfg, timeout_ms=retry_timeout, fast_mode=not deep_check)
            if bool(retry_probe.get("ok")):
                probe = retry_probe
            else:
                d1 = str(probe.get("details", ""))
                d2 = str(retry_probe.get("details", ""))
                probe["details"] = f"{d1} | retry: {d2}"[:180]

        return ProxyCheckResult(
            i,
            raw,
            cfg.server,
            bool(probe.get("ok")),
            int(probe.get("elapsed_ms", 0)),
            str(probe.get("ip", "")),
            str(probe.get("country", "")),
            str(probe.get("details", "")),
        )

    async def _check_proxy_entries(
        self, entries: list[str], base_timeout: int, retry_timeout: int, concurrency: int, deep_check: bool = False
    ) -> list[ProxyCheckResult]:
        sem = asyncio.Semaphore(concurrency)

        async def worker(i: int, raw: str) -> ProxyCheckResult:
            async with sem:
                return await self._probe_proxy_candidate(i, raw, base_timeout, retry_timeout, deep_check=deep_check)

        tasks = [
            asyncio.create_task(worker(i, raw))
            for i, raw in enumerate(entries, start=1)
        ]
        out = await asyncio.gather(*tasks)
        out.sort(key=lambda x: x.index)
        return out

    def _refresh_proxy_country_filter(self, countries: list[str]):
        vals = ["All countries"] + sorted(countries)
        self.proxy_country_filter_menu.configure(values=vals)
        if self.proxy_country_filter_var.get() not in vals:
            self.proxy_country_filter_var.set("All countries")

    def _country_code_from_name(self, country: str) -> str:
        key = self._normalize_country_key(country)
        mapping = {
            "morocco": "MA",
            "algeria": "DZ",
            "tunisia": "TN",
            "egypt": "EG",
            "saudiarabia": "SA",
            "unitedarabemirates": "AE",
            "qatar": "QA",
            "kuwait": "KW",
            "bahrain": "BH",
            "oman": "OM",
            "jordan": "JO",
            "turkey": "TR",
            "france": "FR",
            "spain": "ES",
            "portugal": "PT",
            "germany": "DE",
            "italy": "IT",
            "netherlands": "NL",
            "belgium": "BE",
            "switzerland": "CH",
            "austria": "AT",
            "sweden": "SE",
            "norway": "NO",
            "denmark": "DK",
            "poland": "PL",
            "romania": "RO",
            "greece": "GR",
            "ireland": "IE",
            "unitedkingdom": "GB",
            "canada": "CA",
            "unitedstates": "US",
            "mexico": "MX",
            "brazil": "BR",
            "argentina": "AR",
            "chile": "CL",
            "colombia": "CO",
            "india": "IN",
            "pakistan": "PK",
            "bangladesh": "BD",
            "indonesia": "ID",
            "malaysia": "MY",
            "singapore": "SG",
            "thailand": "TH",
            "vietnam": "VN",
            "china": "CN",
            "japan": "JP",
            "southkorea": "KR",
            "australia": "AU",
            "newzealand": "NZ",
            "southafrica": "ZA",
            "nigeria": "NG",
            "kenya": "KE",
        }
        return mapping.get(key, "")

    def _country_flag(self, country: str) -> str:
        code = self._country_code_from_name(country)
        if len(code) != 2:
            return "??"
        # Unicode regional indicator symbols for country flags.
        return chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))

    def _country_display(self, country: str) -> str:
        if not country:
            return "?? Country N/A"
        return f"{self._country_flag(country)} {country}"

    def _on_remove_unsupported_proxies(self):
        entries = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        cleaned = [x for x in entries if not x.strip().lower().startswith("socks4://")]
        removed = len(entries) - len(cleaned)
        self.proxy_list = cleaned
        self.proxy_list_box.delete("1.0", "end")
        if cleaned:
            self.proxy_list_box.insert("1.0", "\n".join(cleaned))
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})
        self._refresh_proxy_kpis()
        self._set_status(f"Removed {removed} unsupported proxies", THEME.success if removed else THEME.text_muted)

    def _on_keep_country_proxies(self):
        target = self.proxy_country_filter_var.get().strip()
        if not self.proxy_check_results:
            messagebox.showwarning("No check results", "Run Check first.")
            return
        if target == "All countries":
            filtered = [r.raw_input for r in self.proxy_check_results if r.ok]
        else:
            filtered = [r.raw_input for r in self.proxy_check_results if r.ok and r.country == target]
        self.proxy_list = filtered
        self.saved_working_proxies = filtered[:]
        self.proxy_list_box.delete("1.0", "end")
        if filtered:
            self.proxy_list_box.insert("1.0", "\n".join(filtered))
        self._refresh_saved_proxy_menu()
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})
        self._refresh_proxy_kpis()
        self._set_status(f"Kept {len(filtered)} proxies for {target}", THEME.success if filtered else THEME.warning)

    def _on_check_proxies(self):
        entries = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        if not entries:
            messagebox.showwarning("Proxy list empty", "Add proxies first.")
            return
        limit = self._get_max_proxies_to_check(len(entries))
        entries = entries[:limit]
        deep_check = bool(self.proxy_deep_check_var.get())
        base_timeout = self._get_proxy_timeout_ms()
        retry_timeout = int(base_timeout * 1.5)
        self.proxy_list = entries
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})
        self.check_proxy_btn.configure(state="disabled", text="Checking...")

        async def do_check():
            # Parallel checking improves speed; cap to keep machine/network stable.
            concurrency = 8 if len(entries) >= 20 else 6
            return await self._check_proxy_entries(
                entries,
                base_timeout,
                retry_timeout,
                concurrency,
                deep_check=deep_check,
            )

        self._set_status(
            "Proxy check running (deep mode)..." if deep_check else "Proxy check running (fast mode)...",
            THEME.warning,
        )
        self._run_async(do_check(), self._on_check_done)

    def _on_check_done(self, results, error):
        self.check_proxy_btn.configure(state="normal", text="Check")
        if error:
            self._set_status(f"Proxy check error: {error}", THEME.danger)
            return
        self.proxy_check_results = results or []
        ok = [r for r in self.proxy_check_results if r.ok]
        fail = [r for r in self.proxy_check_results if not r.ok]
        countries_ok = sorted({r.country for r in ok if r.country})
        countries_fail = sorted({r.country for r in fail if r.country})
        self._refresh_proxy_country_filter(countries_ok + countries_fail)
        # Keep only verified working proxies in list and persist immediately.
        self.proxy_list = [r.raw_input for r in ok]
        self.proxy_list_box.delete("1.0", "end")
        if self.proxy_list:
            self.proxy_list_box.insert("1.0", "\n".join(self.proxy_list))
        self.saved_working_proxies = [r.raw_input for r in ok]
        self._refresh_saved_proxy_menu()
        best = pick_best_proxy(ok)
        if best:
            best_cfg = parse_proxy_line(best.raw_input)
            if best_cfg:
                self._apply_proxy_config_to_ui(best_cfg)
        self._save_json(PROXY_LIST_FILE, {"items": self.proxy_list, "saved_working": self.saved_working_proxies})
        lines = []
        lines.append("STATUS | # | SERVER | LATENCY | IP | COUNTRY | DETAILS")
        lines.append("-" * 104)
        for r in self.proxy_check_results:
            s = "OK" if r.ok else "FAIL"
            ip = f" | IP {r.ip}" if r.ip else ""
            country = f" | {self._country_display(r.country)}"
            lines.append(f"{s:4} #{r.index:03d} | {r.server} | {r.elapsed_ms}ms{ip}{country} | {r.details}")
        self.proxy_results_box.configure(state="normal")
        self.proxy_results_box.delete("1.0", "end")
        self.proxy_results_box.insert("1.0", "\n".join(lines) if lines else "No results")
        self.proxy_results_box.configure(state="disabled")
        country_stats: dict[str, dict[str, int]] = {}
        for r in self.proxy_check_results:
            label = r.country or "Country N/A"
            if label not in country_stats:
                country_stats[label] = {"ok": 0, "fail": 0}
            if r.ok:
                country_stats[label]["ok"] += 1
            else:
                country_stats[label]["fail"] += 1
        breakdown_lines = []
        for country_name in sorted(country_stats.keys()):
            s = country_stats[country_name]
            breakdown_lines.append(
                f"{self._country_display(country_name if country_name != 'Country N/A' else '')} | OK {s['ok']} | FAIL {s['fail']}"
            )
        self.proxy_country_breakdown_box.configure(state="normal")
        self.proxy_country_breakdown_box.delete("1.0", "end")
        self.proxy_country_breakdown_box.insert(
            "1.0",
            "\n".join(breakdown_lines) if breakdown_lines else "Country breakdown will appear here.",
        )
        self.proxy_country_breakdown_box.configure(state="disabled")
        ok_c = ",".join(countries_ok[:3]) + ("..." if len(countries_ok) > 3 else "")
        fail_c = ",".join(countries_fail[:3]) + ("..." if len(countries_fail) > 3 else "")
        self.proxy_summary_label.configure(
            text=(
                f"Total: {len(self.proxy_check_results)} | OK: {len(ok)} | FAIL: {len(self.proxy_check_results)-len(ok)}"
                f" | OK Countries: {ok_c or 'N/A'} | FAIL Countries: {fail_c or 'N/A'}"
            )
        )
        self._refresh_proxy_kpis()

    def _on_use_best_proxy(self):
        best = pick_best_proxy(self.proxy_check_results)
        if not best:
            return
        cfg = parse_proxy_line(best.raw_input)
        if not cfg:
            return
        self.proxy_enabled_var.set(True)
        self._on_proxy_toggle()
        self.proxy_server_entry.configure(state="normal")
        self.proxy_user_entry.configure(state="normal")
        self.proxy_pass_entry.configure(state="normal")
        self.proxy_server_entry.delete(0, "end")
        self.proxy_server_entry.insert(0, cfg.server)
        self.proxy_user_entry.delete(0, "end")
        self.proxy_user_entry.insert(0, cfg.username)
        self.proxy_pass_entry.delete(0, "end")
        self.proxy_pass_entry.insert(0, cfg.password)

    def _apply_proxy_config_to_ui(self, cfg: ProxyConfig):
        self.proxy_enabled_var.set(True)
        self._on_proxy_toggle()
        self.proxy_server_entry.configure(state="normal")
        self.proxy_user_entry.configure(state="normal")
        self.proxy_pass_entry.configure(state="normal")
        self.proxy_server_entry.delete(0, "end")
        self.proxy_server_entry.insert(0, cfg.server)
        self.proxy_user_entry.delete(0, "end")
        self.proxy_user_entry.insert(0, cfg.username)
        self.proxy_pass_entry.delete(0, "end")
        self.proxy_pass_entry.insert(0, cfg.password)
        self._refresh_proxy_kpis()

    def _on_apply_saved_proxy(self):
        cfg = parse_proxy_line(self.saved_proxy_var.get().strip())
        if not cfg:
            return
        self._apply_proxy_config_to_ui(cfg)

    def _on_export_proxy_results(self):
        if not self.proxy_check_results:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            export_proxy_results_csv(self.proxy_check_results, Path(path))

    def _display_mapping(self, fields):
        for w in self.mapping_scroll.winfo_children():
            w.destroy()
        categories = ["(skip)"] + list(DEFAULT_DATA.keys())
        for idx, f in enumerate(fields):
            row = ctk.CTkFrame(self.mapping_scroll, fg_color=THEME.bg_card)
            row.pack(fill="x", pady=3, padx=3)
            lbl = f"{f.label} [{f.input_type}]"
            if f.matched_category:
                lbl += f" ({f.confidence:.0%})"
            ctk.CTkLabel(row, text=lbl, anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=5)
            var = ctk.StringVar(value=f.matched_category or "(skip)")
            ctk.CTkOptionMenu(row, variable=var, values=categories, width=170, command=lambda v, i=idx: self._on_map_change(i, v)).pack(side="right", padx=8, pady=5)

    def _on_map_change(self, idx, val):
        if self.analysis_result and idx < len(self.analysis_result.fields):
            self.analysis_result.fields[idx].matched_category = None if val == "(skip)" else val

    def _tokenize_text(self, text: str) -> list[str]:
        cleaned = []
        for ch in text.lower():
            cleaned.append(ch if ch.isalnum() else " ")
        return [x for x in "".join(cleaned).split() if x]

    def _ai_best_category_for_field(self, field) -> tuple[str | None, float]:
        haystack = f"{field.label} {field.placeholder} {field.selector} {field.input_type}".lower()
        tokens = set(self._tokenize_text(haystack))
        best_category = None
        best_score = 0.0

        for category, patterns in FIELD_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                plain = (
                    pattern.replace(".?", "")
                    .replace("^", "")
                    .replace("$", "")
                    .replace("\\", "")
                    .lower()
                )
                if plain and plain in haystack:
                    score += 1.0
                pattern_tokens = self._tokenize_text(plain)
                if pattern_tokens:
                    overlap = len(tokens.intersection(pattern_tokens))
                    score += overlap * 0.45
            if score > best_score:
                best_score = score
                best_category = category

        confidence = min(best_score / 3.0, 0.99)
        if confidence < 0.28:
            return None, 0.0
        return best_category, confidence

    def _auto_map_fields(self, fields, force: bool = False) -> tuple[int, int]:
        changed = 0
        for f in fields:
            best_category, confidence = self._ai_best_category_for_field(f)
            if not best_category:
                continue
            should_update = force or (not f.matched_category) or (f.confidence < 0.45)
            if should_update:
                f.matched_category = best_category
                f.confidence = max(f.confidence, confidence)
                changed += 1
        matched = sum(1 for f in fields if f.matched_category)
        return changed, matched

    def _on_ai_auto_map(self):
        if not self.analysis_result:
            messagebox.showwarning("Analyze first", "Run Analyze before AI Auto Map.")
            return

        changed, matched = self._auto_map_fields(self.analysis_result.fields, force=False)
        self._display_mapping(self.analysis_result.fields)
        self.preview_btn.configure(state="normal" if matched else "disabled")
        self.fill_btn.configure(state="normal" if matched else "disabled")
        self._set_status(f"AI Auto Map updated {changed} fields", THEME.success)
        self._append_report("ai_auto_map", "ok", f"changed={changed}, matched={matched}")

    def _on_ai_suggest_data(self):
        current = self._collect_data()
        selected_country = self.fake_country_var.get().strip() if hasattr(self, "fake_country_var") else ""
        if selected_country and selected_country != "Auto (country field)":
            country_values = [selected_country]
        else:
            country_values = self._parse_list_values(current.get("country", ""))
        suggested = self._build_fake_profile_data(preferred_countries=country_values or None)

        filled = 0
        for key, value in current.items():
            if str(value).strip():
                continue
            current[key] = suggested.get(key, "")
            filled += 1

        self._apply_data_to_form(current)
        self._sync_profile()
        self._save_runtime()
        self._set_status(f"AI Suggest Data filled {filled} empty fields", THEME.success)
        self._append_report("ai_suggest_data", "ok", f"filled={filled}")

    def _on_clear_fields(self):
        for k, w in self.data_entries.items():
            if isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
            else:
                w.delete(0, "end")
        self._set_status("All fields cleared", THEME.success)

    def _on_reset_sequential(self):
        self.sequential_indices.clear()
        self._set_status("Sequential indices reset", THEME.success)

    def _on_open_sessions_folder(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._open_local_path(SESSIONS_DIR)

    def _on_export_profiles_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        import csv
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["profile", "first_name", "last_name", "email", "phone", "country", "device", "fill_mode"])
            for name, p in self.profiles.items():
                ud = p.get("user_data", {})
                st = p.get("settings", {})
                writer.writerow([
                    name,
                    ud.get("first_name", ""),
                    ud.get("last_name", ""),
                    ud.get("email", ""),
                    ud.get("phone", ""),
                    ud.get("country", ""),
                    st.get("device_profile", ""),
                    st.get("fill_mode", ""),
                ])
        self._set_status(f"Exported {len(self.profiles)} profiles to CSV", THEME.success)

    def _on_about(self):
        pop = ctk.CTkToplevel(self)
        pop.title("About ClickOffres AutoBot")
        pop.geometry("440x300")
        pop.resizable(False, False)
        pop.configure(fg_color=THEME.bg_card)
        frame = ctk.CTkFrame(pop, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=24, pady=24)
        ctk.CTkLabel(
            frame,
            text="ClickOffres AutoBot",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=THEME.text_primary,
        ).pack(anchor="center", pady=(0, 4))
        ctk.CTkLabel(
            frame,
            text="v1.0",
            font=ctk.CTkFont(size=14),
            text_color=THEME.text_muted,
        ).pack(anchor="center", pady=(0, 16))
        ctk.CTkLabel(
            frame,
            text="Application pour QA/testing legal de formulaires web.",
            font=ctk.CTkFont(size=12),
            text_color=THEME.text_muted,
        ).pack(anchor="center", pady=(0, 4))
        ctk.CTkLabel(
            frame,
            text="Usage légal uniquement — pas de spoofing, pas de bypass.",
            font=ctk.CTkFont(size=12),
            text_color=THEME.text_muted,
        ).pack(anchor="center", pady=(0, 20))
        ctk.CTkLabel(
            frame,
            text="Telegram: werlist99",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=THEME.accent,
        ).pack(anchor="center", pady=(0, 20))
        ctk.CTkButton(frame, text="Close", command=pop.destroy, width=120).pack(anchor="center")

    def _build_runtime_data(self, commit=True):
        runtime, next_idx = {}, {}
        mode = self.fill_mode_var.get()
        for k, raw in self.user_data.items():
            if k == "message":
                runtime[k] = raw
                continue
            vals = self._parse_list_values(raw)
            if not vals:
                runtime[k] = ""
            elif len(vals) == 1:
                runtime[k] = vals[0]
            elif mode == "sequential":
                i = self.sequential_indices.get(k, 0) % len(vals)
                runtime[k] = vals[i]
                next_idx[k] = i + 1
                if commit:
                    self.sequential_indices[k] = i + 1
            else:
                runtime[k] = random.choice(vals)
        return runtime, next_idx

    def _on_open_login_session(self):
        url = self._normalize_url(self.login_url_entry.get())
        if not url:
            messagebox.showwarning("Login URL required", "Enter login URL first.")
            return
        self._on_save_data()
        proxy = self._collect_proxy()
        proxy_val = proxy if proxy.is_valid else None
        device = self._get_selected_devices()[0]
        self.login_btn.configure(state="disabled", text="Opening...")

        async def do_open():
            await self.engine.start_browser(headless=False, proxy=proxy_val, device_profile_name=device)
            return await self.engine.navigate(url)

        self._run_async(do_open(), self._on_open_login_done)

    def _on_open_login_done(self, _title, error):
        self.login_btn.configure(state="normal", text="Open Login Session")
        if error:
            self._set_status(f"Login error: {error}", THEME.danger)
            return
        self._set_status("Login page opened", THEME.success)

    def _on_save_session(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        default_name = f"{self.current_profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = filedialog.asksaveasfilename(initialdir=str(SESSIONS_DIR), initialfile=default_name, defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return

        async def do_save():
            await self.engine.save_storage_state(path)
            return path

        self._run_async(do_save(), self._on_save_session_done)

    def _on_save_session_done(self, _path, error):
        if error:
            self._set_status(f"Save session error: {error}", THEME.danger)
            return
        self._set_status("Session saved", THEME.success)

    def _on_load_session(self):
        path = filedialog.askopenfilename(initialdir=str(SESSIONS_DIR), filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        target = self._normalize_url(self.url_entry.get()) or self._normalize_url(self.login_url_entry.get()) or "https://example.com"
        proxy = self._collect_proxy()
        proxy_val = proxy if proxy.is_valid else None
        device = self._get_selected_devices()[0]

        async def do_load():
            await self.engine.start_browser(headless=False, proxy=proxy_val, device_profile_name=device, storage_state_path=path)
            return await self.engine.navigate(target)

        self._run_async(do_load(), self._on_load_session_done)

    def _on_load_session_done(self, _title, error):
        if error:
            self._set_status(f"Load session error: {error}", THEME.danger)
            return
        self._set_status("Session loaded", THEME.success)

    def _on_smart_run(self):
        url = self._normalize_url(self.url_entry.get())
        if not url:
            messagebox.showwarning("URL required", "Enter target URL.")
            return
        self._on_save_data()
        self.preview_btn.configure(state="disabled")
        self.fill_btn.configure(state="disabled")
        self.submit_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.smart_run_btn.configure(state="disabled", text="Smart Running...")
        self.stop_smart_run_btn.configure(state="normal")
        self.pause_smart_run_btn.configure(state="normal", text="Pause")
        self.smart_run_cancel_requested = False
        self.smart_run_paused = False
        self.last_smart_run_details = []
        self.progress.set(0)
        self._set_status("Smart run started...", THEME.warning)

        entries = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        entries = entries[: self._get_max_proxies_to_check(len(entries))]
        fallback_proxy = self._collect_proxy()
        fallback_proxy_val = fallback_proxy if fallback_proxy.is_valid else None
        devices = self._get_selected_devices()
        safe_mode_enabled = self.safe_mode_var.get()
        ai_flow_enabled = self.smart_ai_flow_var.get() and not safe_mode_enabled
        auto_submit_enabled = self.auto_submit_var.get() and not safe_mode_enabled
        assist_clicks_enabled = self.smart_assist_clicks_var.get() and not safe_mode_enabled
        browser_delay_seconds = self._get_browser_delay_seconds()
        base_timeout = self._get_proxy_timeout_ms()
        retry_timeout = int(base_timeout * 1.5)
        self.user_data = self._collect_data()
        runtime, _ = self._build_runtime_data(commit=True)

        def on_progress(cur, total, _label, _status):
            self.after(0, lambda: self.progress.set(cur / total if total else 0))

        async def do_smart():
            proxy_results = []
            selected_proxy = fallback_proxy_val
            selected_proxy_raw = ""
            try:
                if entries:
                    self.after(0, lambda: self._set_status(f"Checking proxies: {len(entries)} target(s)...", THEME.warning))
                    proxy_results = await self._check_proxy_entries(
                        entries, base_timeout, retry_timeout, concurrency=6, deep_check=False
                    )
                    if self.smart_run_cancel_requested:
                        raise RuntimeError("Smart run cancelled by user.")

                if proxy_results:
                    best = pick_best_proxy(proxy_results)
                    if best:
                        best_cfg = parse_proxy_line(best.raw_input)
                        if best_cfg and best_cfg.is_valid:
                            selected_proxy = best_cfg
                            selected_proxy_raw = best.raw_input

                runs = []
                for device_idx, device_name in enumerate(devices):
                    await self._wait_if_paused()
                    if self.smart_run_cancel_requested:
                        raise RuntimeError("Smart run cancelled by user.")
                    self.after(
                        0,
                        lambda idx=device_idx, total=len(devices), dev=device_name: self._set_status(
                            f"Running browser {idx + 1}/{total} ({dev})...", THEME.warning
                        ),
                    )
                    await self.engine.start_browser(
                        headless=False,
                        proxy=selected_proxy,
                        device_profile_name=device_name,
                    )
                    helper_actions = []
                    if ai_flow_enabled and assist_clicks_enabled:
                        helper_actions.extend(await self.engine.click_helper_elements(max_clicks=8))
                    analysis = await self.engine.analyze(url)
                    matched = sum(1 for f in analysis.fields if f.matched_category)
                    if ai_flow_enabled and matched == 0:
                        # Fallback auto-mapping to avoid empty fill plans on noisy forms.
                        _changed, matched = self._auto_map_fields(analysis.fields, force=True)
                    if ai_flow_enabled and assist_clicks_enabled and matched == 0:
                        # Retry one smart click pass then re-analyze.
                        helper_actions.extend(await self.engine.click_helper_elements(max_clicks=6))
                        analysis = await self.engine.analyze(url)
                        matched = sum(1 for f in analysis.fields if f.matched_category)
                        if matched == 0:
                            _changed, matched = self._auto_map_fields(analysis.fields, force=True)
                    fill_results = []
                    submit_ok = None
                    if matched:
                        if self.smart_run_cancel_requested:
                            raise RuntimeError("Smart run cancelled by user.")
                        fill_results = await self.engine.fill_fields(analysis.fields, runtime, on_progress)
                        if auto_submit_enabled:
                            submit_ok = await self.engine.submit_form()
                    runs.append(
                        {
                            "device": device_name,
                            "analysis": analysis,
                            "matched": matched,
                            "fill_results": fill_results,
                            "submit_ok": submit_ok,
                            "helper_actions": helper_actions,
                        }
                    )
                    if browser_delay_seconds > 0 and device_idx < len(devices) - 1:
                        self.after(
                            0,
                            lambda s=browser_delay_seconds: self._set_status(
                                f"Waiting {s}s before next browser...", THEME.warning
                            ),
                        )
                        await self._sleep_interruptible(browser_delay_seconds)
                return {
                    "proxy_results": proxy_results,
                    "selected_proxy_raw": selected_proxy_raw,
                    "runs": runs,
                    "safe_mode_enabled": safe_mode_enabled,
                    "ai_flow_enabled": ai_flow_enabled,
                    "browser_delay_seconds": browser_delay_seconds,
                    "browser_closed": True,
                }
            finally:
                # Always close browser when smart run finishes/cancels/errors.
                try:
                    await self.engine.close()
                except Exception:
                    pass

        self._run_async(do_smart(), self._on_smart_run_done)

    def _on_smart_run_done(self, payload, error):
        self.analyze_btn.configure(state="normal")
        self.smart_run_btn.configure(state="normal", text="Smart Run")
        self.stop_smart_run_btn.configure(state="disabled")
        self.pause_smart_run_btn.configure(state="disabled", text="Pause")
        if error:
            err_text = str(error)
            if "cancelled by user" in err_text.lower():
                self._set_status("Smart run stopped", THEME.warning)
                self._append_report("smart_run", "warn", "stopped_by_user")
                return
            self._set_status(f"Smart run error: {error}", THEME.danger)
            self._append_report("smart_run", "error", err_text)
            return

        proxy_results = payload.get("proxy_results", [])
        selected_proxy_raw = payload.get("selected_proxy_raw", "")
        if proxy_results:
            self._on_check_done(proxy_results, None)
        if selected_proxy_raw:
            cfg = parse_proxy_line(selected_proxy_raw)
            if cfg:
                self._apply_proxy_config_to_ui(cfg)

        runs = payload.get("runs", [])
        safe_mode_enabled = bool(payload.get("safe_mode_enabled", False))
        ai_flow_enabled = bool(payload.get("ai_flow_enabled", False))
        browser_delay_seconds = int(payload.get("browser_delay_seconds", 0))
        if not runs:
            self._set_status("Smart run finished with no selected devices", THEME.warning)
            self._append_report("smart_run", "warn", "no device selected")
            return

        first_run = runs[0]
        self.analysis_result = first_run["analysis"]
        self._display_mapping(self.analysis_result.fields)

        total_fields = sum(len(x["analysis"].fields) for x in runs)
        total_matched = sum(int(x["matched"]) for x in runs)
        total_filled = 0
        total_skipped = 0
        total_errors = 0
        total_submitted = 0
        total_helper_clicks = 0
        for run in runs:
            fill_results = run.get("fill_results", [])
            helper_actions = run.get("helper_actions", [])
            total_filled += sum(1 for r in fill_results if r.get("status") == "filled")
            total_skipped += sum(1 for r in fill_results if r.get("status") == "skipped")
            total_errors += sum(1 for r in fill_results if r.get("status") == "error")
            if run.get("submit_ok") is True:
                total_submitted += 1
            total_helper_clicks += len(helper_actions)
            self.last_smart_run_details.append(
                (
                    f"{run['device']}: fields={len(run['analysis'].fields)}, "
                    f"matched={run['matched']}, filled={sum(1 for r in fill_results if r.get('status') == 'filled')}, "
                    f"clicks={len(helper_actions)}, submit={'yes' if run.get('submit_ok') else 'no'}"
                )
            )

        if total_matched and total_filled >= 0:
            self.preview_btn.configure(state="normal")
            self.fill_btn.configure(state="normal")
            self.submit_btn.configure(state="normal")
            self.progress.set(1)
            self._set_status(
                (
                    f"Smart run done on {len(runs)} device(s): "
                    f"{total_filled} filled, {total_skipped} skipped, {total_errors} errors, "
                    f"{total_helper_clicks} clicks, {total_submitted} submitted | browser closed"
                ),
                THEME.success,
            )
            self._append_report(
                "smart_run",
                "ok",
                (
                    f"devices={len(runs)}, fields={total_fields}, "
                    f"matched={total_matched}, filled={total_filled}, clicks={total_helper_clicks}, "
                    f"submitted={total_submitted}, safe_mode={safe_mode_enabled}, "
                    f"ai_flow={ai_flow_enabled}, delay={browser_delay_seconds}s"
                ),
            )
        else:
            self.preview_btn.configure(state="disabled")
            self.fill_btn.configure(state="disabled")
            self.submit_btn.configure(state="disabled")
            self.progress.set(1)
            self._set_status(
                f"Smart run finished on {len(runs)} device(s): {total_fields} fields, 0 matched",
                THEME.warning,
            )
            self._append_report(
                "smart_run",
                "warn",
                f"devices={len(runs)}, fields={total_fields}, matched=0",
            )
        self._show_panel("platform")

    def _on_stop_smart_run(self):
        self.smart_run_cancel_requested = True
        self.smart_run_paused = False
        self.pause_smart_run_btn.configure(text="Pause")
        self.stop_smart_run_btn.configure(state="disabled")
        self._set_status("Stopping smart run...", THEME.warning)

    def _on_pause_resume_smart_run(self):
        self.smart_run_paused = not self.smart_run_paused
        if self.smart_run_paused:
            self.pause_smart_run_btn.configure(text="Resume")
            self._set_status("Smart run paused", THEME.warning)
        else:
            self.pause_smart_run_btn.configure(text="Pause")
            self._set_status("Smart run resumed", THEME.success)

    def _on_reload_fake_lists(self):
        self.fake_lists = self._load_fake_lists()
        self.country_presets = self._load_country_presets()
        if hasattr(self, "fake_country_menu"):
            choices = ["Auto (country field)"] + sorted(self.fake_lists.get("countries", []))
            self.fake_country_menu.configure(values=choices)
            if self.fake_country_var.get() not in choices:
                self.fake_country_var.set("Auto (country field)")
        self._set_status("Fake data lists reloaded", THEME.success)

    def _open_local_path(self, path: Path):
        try:
            os.startfile(str(path))
        except Exception:
            messagebox.showinfo("Open path", f"Path: {path}")

    def _on_open_fake_data_folder(self):
        FAKE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._open_local_path(FAKE_DATA_DIR)

    def _on_open_country_presets_file(self):
        self.country_presets = self._load_country_presets()
        if not COUNTRY_PRESETS_FILE.exists():
            COUNTRY_PRESETS_FILE.write_text("{}", encoding="utf-8")
        self._open_local_path(COUNTRY_PRESETS_FILE)

    def _on_show_run_details(self):
        details = self.last_smart_run_details or ["No smart run details yet."]
        pop = ctk.CTkToplevel(self)
        pop.title("Smart Run Details")
        pop.geometry("820x480")
        box = ctk.CTkTextbox(pop)
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", "\n".join(details))
        box.configure(state="disabled")

    def _on_platform_tool_menu(self, choice: str):
        action = (choice or "").strip()
        if action == "Run Details":
            self._on_show_run_details()
        elif action == "Reload Fake Lists":
            self._on_reload_fake_lists()
        elif action == "Health Check":
            self._on_health_check()
        elif action == "Quick Run":
            self._on_quick_run()
        elif action == "AI Auto Map":
            self._on_ai_auto_map()
        elif action == "AI Suggest Data":
            self._on_ai_suggest_data()
        elif action == "Export Profiles":
            self._on_export_profiles()
        elif action == "Import Profiles":
            self._on_import_profiles()
        elif action == "Clear All Fields":
            self._on_clear_fields()
        elif action == "Reset Sequential Indices":
            self._on_reset_sequential()
        elif action == "Open Sessions Folder":
            self._on_open_sessions_folder()
        elif action == "Export Profiles CSV":
            self._on_export_profiles_csv()
        elif action == "About":
            self._on_about()
        if hasattr(self, "platform_tools_var"):
            self.platform_tools_var.set("Tools")

    def _on_health_check(self):
        target_url = self._normalize_url(self.url_entry.get())
        selected_devices = self._get_selected_devices()
        data = self._collect_data()
        required_keys = ["first_name", "last_name", "email", "phone", "country"]
        missing = [k for k in required_keys if not str(data.get(k, "")).strip()]

        current_proxies = normalize_proxy_entries(self.proxy_list_box.get("1.0", "end-1c"))
        working_count = len(self.saved_working_proxies)
        fake_files_present = 0
        for file_name in FAKE_LIST_FILES.values():
            if (FAKE_DATA_DIR / file_name).exists():
                fake_files_present += 1

        checks = [
            ("Target URL", bool(target_url), target_url or "Missing"),
            ("Selected devices", bool(selected_devices), ", ".join(selected_devices) if selected_devices else "None"),
            ("Required profile fields", not missing, "OK" if not missing else f"Missing: {', '.join(missing)}"),
            ("Proxy list", bool(current_proxies), f"{len(current_proxies)} entries"),
            ("Working proxies", working_count > 0, f"{working_count} saved working"),
            ("Fake data files", fake_files_present >= 8, f"{fake_files_present}/{len(FAKE_LIST_FILES)} found"),
        ]

        ok_count = sum(1 for _, ok, _ in checks if ok)
        lines = []
        for label, ok, details in checks:
            icon = "PASS" if ok else "FAIL"
            lines.append(f"{icon} | {label}: {details}")
        lines.append("")
        lines.append(f"Score: {ok_count}/{len(checks)}")

        messagebox.showinfo("Health Check", "\n".join(lines))
        status = "ok" if ok_count == len(checks) else "warn"
        self._append_report("health_check", status, f"score={ok_count}/{len(checks)}")
        if status == "ok":
            self._set_status("Health check passed", THEME.success)
        else:
            self._set_status("Health check has warnings", THEME.warning)

    def _on_quick_run(self):
        self._on_generate_fake_data()
        self.after(100, self._on_smart_run)

    def _on_analyze(self):
        url = self._normalize_url(self.url_entry.get())
        if not url:
            messagebox.showwarning("URL required", "Enter target URL.")
            return
        self._on_save_data()
        self.preview_btn.configure(state="disabled")
        self.fill_btn.configure(state="disabled")
        self.submit_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.progress.set(0)
        self._set_status("Analyzing...", THEME.warning)
        proxy = self._collect_proxy()
        proxy_val = proxy if proxy.is_valid else None
        device = self.device_profile_var.get()

        async def do_analyze():
            if not await self.engine.has_live_page():
                await self.engine.start_browser(headless=False, proxy=proxy_val, device_profile_name=device)
            return await self.engine.analyze(url)

        self._run_async(do_analyze(), self._on_analyze_done)

    def _on_analyze_done(self, result, error):
        self.analyze_btn.configure(state="normal", text="Analyze")
        if error:
            self._set_status(f"Analyze error: {error}", THEME.danger)
            self._append_report("analyze", "error", str(error))
            return
        self.analysis_result = result
        # Auto-strengthen mapping if analyzer returned weak/no matches.
        initial_matched = sum(1 for f in result.fields if f.matched_category)
        if initial_matched == 0:
            self._auto_map_fields(result.fields, force=True)
        self._display_mapping(result.fields)
        matched = sum(1 for f in result.fields if f.matched_category)
        self.preview_btn.configure(state="normal" if matched else "disabled")
        self.fill_btn.configure(state="normal" if matched else "disabled")
        self.progress.set(1)
        self._set_status(f"Found {len(result.fields)} fields ({matched} matched)", THEME.success)
        self._append_report("analyze", "ok", f"fields={len(result.fields)}, matched={matched}")
        self._show_panel("platform")

    def _on_preview_fill(self):
        if not self.analysis_result:
            return
        self.user_data = self._collect_data()
        runtime, _ = self._build_runtime_data(commit=False)
        pop = ctk.CTkToplevel(self)
        pop.title("Dry Run Preview")
        pop.geometry("900x560")
        box = ctk.CTkTextbox(pop)
        box.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        lines = []
        for i, f in enumerate(self.analysis_result.fields, start=1):
            if not f.matched_category:
                lines.append(f"{i:03d}. SKIP | {f.label} | no category")
                continue
            val = runtime.get(f.matched_category, "")
            if not val:
                lines.append(f"{i:03d}. SKIP | {f.label} | empty value")
            else:
                lines.append(f"{i:03d}. FILL | {f.label} | {f.matched_category} | {val[:70]}")
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")
        row = ctk.CTkFrame(pop, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(row, text="Confirm Fill", command=lambda: (pop.destroy(), self._run_fill())).pack(side="right")
        ctk.CTkButton(row, text="Cancel", command=pop.destroy).pack(side="right", padx=8)

    def _on_fill(self):
        if self.analysis_result:
            self._run_fill()

    def _run_fill(self):
        self.user_data = self._collect_data()
        runtime, _ = self._build_runtime_data(commit=True)
        self.fill_btn.configure(state="disabled", text="Filling...")
        self.preview_btn.configure(state="disabled")
        self.progress.set(0)
        self._set_status("Filling...", THEME.warning)

        def on_progress(cur, total, _label, _status):
            self.after(0, lambda: self.progress.set(cur / total if total else 0))

        async def do_fill():
            return await self.engine.fill_fields(self.analysis_result.fields, runtime, on_progress)

        self._run_async(do_fill(), self._on_fill_done)

    def _on_fill_done(self, results, error):
        self.fill_btn.configure(state="normal", text="Fill")
        self.preview_btn.configure(state="normal")
        if error:
            self._set_status(f"Fill error: {error}", THEME.danger)
            self._append_report("fill", "error", str(error))
            return
        filled = sum(1 for r in results if r.get("status") == "filled")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        errors = sum(1 for r in results if r.get("status") == "error")
        self.submit_btn.configure(state="normal")
        self.progress.set(1)
        self._set_status(f"Fill done: {filled} filled, {skipped} skipped, {errors} errors", THEME.success)
        self._append_report("fill", "ok", f"filled={filled}, skipped={skipped}, errors={errors}")

    def _on_submit(self):
        if not self.analysis_result:
            return
        if not messagebox.askyesno("Confirm submit", "Submit form now?"):
            return
        self.submit_btn.configure(state="disabled", text="Submitting...")
        self._set_status("Submitting...", THEME.warning)

        async def do_submit():
            return await self.engine.submit_form()

        self._run_async(do_submit(), self._on_submit_done)

    def _on_submit_done(self, ok, error):
        self.submit_btn.configure(state="normal", text="Submit")
        if error:
            self._set_status(f"Submit error: {error}", THEME.danger)
            self._append_report("submit", "error", str(error))
            return
        if ok:
            self._set_status("Form submitted", THEME.success)
            self._append_report("submit", "ok", "submitted")
        else:
            self._set_status("Submit button not found", THEME.warning)
            self._append_report("submit", "warn", "no submit button")

    def _on_export_reports(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self._save_json(Path(path), self.run_history)

    def _on_clear_reports(self):
        if not messagebox.askyesno("Clear reports", "Delete all report history?"):
            return
        self.run_history = []
        self._save_json(REPORTS_FILE, self.run_history)
        self._refresh_reports()
        self._set_status("Reports cleared", THEME.success)

    def _on_clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._set_status("Logs cleared", THEME.success)

    def _refresh_reports(self):
        if not hasattr(self, "reports_box"):
            return
        lines = [f"{x['time']} | {x['event']} | {x['status']} | {x['details']}" for x in self.run_history[-250:]]
        self.reports_box.delete("1.0", "end")
        self.reports_box.insert("1.0", "\n".join(lines) if lines else "No reports yet.")
        if hasattr(self, "report_total_label"):
            total = len(self.run_history)
            ok_warn = len([x for x in self.run_history if str(x.get("status", "")).lower() in ("ok", "warn")])
            errors = len([x for x in self.run_history if str(x.get("status", "")).lower() == "error"])
            self.report_total_label.configure(text=f"Total\n{total}")
            self.report_ok_label.configure(text=f"OK/Warn\n{ok_warn}")
            self.report_error_label.configure(text=f"Errors\n{errors}")

    def on_closing(self):
        try:
            self._on_save_data()
        except Exception:
            pass
        asyncio.run_coroutine_threadsafe(self.engine.close(), self.loop)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
