import json, io, os
import streamlit as st
from services.storage import *
from services.google_places import text_search, get_place_details, photo_bytes
from services.geocoding import geocode
from models.restaurant import Restaurant
from utils.security import generate_recovery_code, valid_pin, hash_secret, verify_secret
from utils.validation import clean_name, clean_collection_name, validate_backup_bytes
from utils.ranking import rank_restaurants, top_pick_labels
from utils.distance import format_distance
from utils.cuisine import CANONICAL_CUISINES, normalize_cuisine, translate_cuisine
from i18n.translations import t, TRANSLATIONS, missing_keys

st.set_page_config(page_title="RestaurantRank", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")

THEMES={
"rose":{"primary":"#e85d9b","secondary":"#f7c5da","bg":"#fff7fb","surface":"#ffffff","text":"#251923","muted":"#776875","border":"#f0d8e5","accent":"#ff8fbd"},
"ocean":{"primary":"#1677ff","secondary":"#b9dbff","bg":"#f5faff","surface":"#ffffff","text":"#172033","muted":"#657083","border":"#dce8f6","accent":"#4db5ff"},
"fresh":{"primary":"#16a36a","secondary":"#bdeed8","bg":"#f5fff9","surface":"#ffffff","text":"#10241b","muted":"#64766e","border":"#d9eee5","accent":"#56d49c"},
"purple":{"primary":"#7b61ff","secondary":"#d8d0ff","bg":"#faf8ff","surface":"#ffffff","text":"#211c35","muted":"#716b82","border":"#e6e1f7","accent":"#ad9aff"},
"sunset":{"primary":"#ef7d32","secondary":"#ffd1ad","bg":"#fff9f4","surface":"#ffffff","text":"#2a211b","muted":"#7b6b5f","border":"#f2dfd1","accent":"#ffae78"}}

if "page" not in st.session_state: st.session_state.page="search"
if "profile_id" not in st.session_state: st.session_state.profile_id=None
if "unlocked" not in st.session_state: st.session_state.unlocked=False
if "recovery_pid" not in st.session_state: st.session_state.recovery_pid=None
if "pending_recovery" not in st.session_state: st.session_state.pending_recovery=None
if "results" not in st.session_state: st.session_state.results=[]
if "location" not in st.session_state: st.session_state.location=None
if "compare" not in st.session_state: st.session_state.compare=[]
if "query_food" not in st.session_state: st.session_state.query_food=""


def current_profile(): return get_profile(st.session_state.profile_id) if st.session_state.profile_id else None

def lang():
    p=current_profile(); return p["language"] if p else st.session_state.get("lang","en")

def tx(key,**kw): return t(key,lang(),**kw)

def apply_css():
    p=current_profile(); theme=THEMES.get(p["theme"] if p else "ocean",THEMES["ocean"])
    appearance=p["appearance"] if p else "system"
    dark = appearance=="dark"
    if appearance=="system": dark=False
    bg="#11151c" if dark else theme["bg"]; surface="#191f29" if dark else theme["surface"]; text="#f5f7fa" if dark else theme["text"]; muted="#aeb7c6" if dark else theme["muted"]; border="#2f3948" if dark else theme["border"]
    st.markdown(f"""
    <style>
    :root{{--rr-primary:{theme['primary']};--rr-bg:{bg};--rr-surface:{surface};--rr-text:{text};--rr-muted:{muted};--rr-border:{border};--rr-accent:{theme['accent']};}}
    html,body,[data-testid='stAppViewContainer']{{background:var(--rr-bg);color:var(--rr-text)}}
    [data-testid='stHeader']{{background:transparent}}
    .block-container{{max-width:1180px;padding:1.2rem 1rem 6rem}}
    .rr-hero{{padding:1.2rem 0 .6rem}}
    .rr-title{{font-size:clamp(2rem,7vw,3.2rem);font-weight:850;letter-spacing:-.04em;margin:0;color:var(--rr-text)}}
    .rr-sub{{font-size:1rem;color:var(--rr-muted);margin:.25rem 0 1rem}}
    .rr-card{{background:var(--rr-surface);border:1px solid var(--rr-border);border-radius:22px;padding:1rem;box-shadow:0 8px 26px rgba(0,0,0,.05);height:100%}}
    .rr-chip{{display:inline-block;padding:.38rem .66rem;border-radius:999px;background:var(--rr-bg);border:1px solid var(--rr-border);margin:.18rem .15rem;font-size:.86rem}}
    .rr-score{{font-size:1.5rem;font-weight:850;color:var(--rr-primary)}}
    .rr-muted{{color:var(--rr-muted)}}
    .rr-badge{{display:inline-block;padding:.28rem .55rem;border-radius:999px;background:var(--rr-primary);color:white;font-weight:750;font-size:.76rem}}
    [data-testid='stButton'] button,[data-testid='stDownloadButton'] button{{border-radius:14px;min-height:44px;font-weight:700}}
    div[data-baseweb='input'] input,div[data-baseweb='select']>div,textarea{{border-radius:14px!important}}
    @media(max-width:768px){{.block-container{{padding:.75rem .7rem 6rem}}.rr-card{{border-radius:18px;padding:.9rem}}.rr-title{{font-size:2.15rem}}}}
    </style>
    """,unsafe_allow_html=True)

apply_css()


def header():
    p=current_profile(); st.markdown(f"<div class='rr-hero'><div class='rr-title'>🍽️ RestaurantRank</div><div class='rr-sub'>{tx('app.tagline')}</div></div>",unsafe_allow_html=True)
    if p: st.caption(f"👤 {p['name']}")

def profile_gate():
    header()
    if st.session_state.pending_recovery:
        pid,recovery=st.session_state.pending_recovery
        p=get_profile(pid)
        st.success("Profile created successfully. Save this recovery code somewhere safe before continuing.")
        st.code(recovery)
        st.download_button("Download recovery file",f"RestaurantRank recovery code for {p['name']}: {recovery}\nKeep this private. It does not contain your PIN.\n",file_name="restaurant_rank_recovery.txt",mime="text/plain")
        if st.button("I've saved it — Continue",type="primary",use_container_width=True):
            st.session_state.pending_recovery=None; st.session_state.profile_id=pid; st.session_state.unlocked=True; st.rerun()
        return
    profiles=list_profiles()
    if st.session_state.recovery_pid:
        pid=st.session_state.recovery_pid
        st.subheader(tx("profile.recover"))
        code=st.text_input(tx("profile.code"),max_chars=14)
        new=st.text_input(tx("profile.new_pin"),type="password",max_chars=4)
        if st.button(tx("profile.recover_btn"),use_container_width=True):
            if not verify_secret(code.strip().upper(),get_profile(pid)["recovery_hash"]): st.error(tx("security.recovery_bad"))
            elif not valid_pin(new): st.error("PIN must be exactly 4 digits.")
            else:
                change_pin(pid,new); st.session_state.recovery_pid=None; st.session_state.profile_id=pid; st.session_state.unlocked=True; st.rerun()
        if st.button("←"): st.session_state.recovery_pid=None; st.rerun()
        return
    if profiles:
        st.markdown(f"### {tx('profile.who')}")
        cols=st.columns(min(3,len(profiles)))
        for i,row in enumerate(profiles):
            with cols[i%len(cols)]:
                st.markdown(f"<div class='rr-card'><div style='font-size:2rem'>👤</div><h3>{row['name']}</h3></div>",unsafe_allow_html=True)
                if st.button(tx("profile.continue"),key=f"pick_{row['id']}",use_container_width=True): st.session_state.selected_profile=row['id']
        selected=st.session_state.get("selected_profile")
        if selected:
            row=get_profile(selected); pin=st.text_input(tx("profile.pin"),type="password",max_chars=4,key="login_pin")
            c1,c2=st.columns(2)
            with c1:
                if st.button(tx("profile.continue"),use_container_width=True):
                    ok,status=authenticate_pin(selected,pin)
                    if ok: st.session_state.profile_id=selected; st.session_state.unlocked=True; st.session_state.pop("selected_profile",None); st.rerun()
                    elif status=="locked": st.error(tx("security.locked"))
                    else: st.error(tx("security.wrong"))
            with c2:
                if st.button(tx("profile.forgot"),use_container_width=True): st.session_state.recovery_pid=selected; st.rerun()
        st.divider()
    else:
        st.info(tx("profile.create"))
    with st.expander("＋ "+tx("profile.create"),expanded=not bool(profiles)):
        name=st.text_input(tx("profile.name"),max_chars=50)
        pin=st.text_input(tx("profile.pin"),type="password",max_chars=4)
        pin2=st.text_input(tx("profile.confirm_pin"),type="password",max_chars=4)
        if st.button(tx("profile.create_btn"),use_container_width=True):
            try:
                nm=clean_name(name)
                if not valid_pin(pin) or pin!=pin2: raise ValueError("PIN must be exactly 4 digits and both PIN entries must match.")
                recovery=generate_recovery_code(); pid=create_profile(nm,pin,recovery); st.session_state.pending_recovery=(pid,recovery); st.rerun()
            except Exception as e: st.error(str(e))


def nav():
    p=current_profile()
    if not p:return
    labels=[(tx("nav.search"),"search","🔍"),(tx("nav.favorites"),"favorites","❤️"),(tx("nav.compare"),"compare","⚖️"),(tx("nav.profile"),"profile","👤")]
    st.markdown("<div style='height:2px'></div>",unsafe_allow_html=True)
    cols=st.columns(4)
    for i,(label,page,icon) in enumerate(labels):
        with cols[i]:
            if st.button(f"{icon} {label}",key=f"nav_{page}",use_container_width=True): st.session_state.page=page; st.rerun()
    st.divider()


def resolve_location(query):
    if not query.strip(): return None
    locs=geocode(query.strip())
    if not locs:return None
    if len(locs)>1 and not st.session_state.get("confirmed_location"):
        st.session_state.location_candidates=locs
        return "AMBIGUOUS"
    return locs[0]


def search_page():
    header()
    p=current_profile(); default_radius=p["default_radius"] if p else 5
    loc_text=st.text_input(tx("home.where"),value=st.session_state.get("search_location",""),placeholder="Houston, Cypress, 77002")
    cuisine_options=["All Food Types"]+CANONICAL_CUISINES
    prior_food=st.session_state.get("query_food_list",[])
    food=st.multiselect(tx("home.mood"),cuisine_options,default=prior_food,placeholder="Choose one or more food types")
    rcol1,rcol2=st.columns([2,1]);
    with rcol1: radius=st.select_slider(tx("home.radius"),options=[1,3,5,10,15,25],value=default_radius)
    with rcol2:
        if st.button("📍 "+tx("home.near"),use_container_width=True): st.info(tx("location.denied"))
    quick=[("🍕","Pizza"),("🌮","Mexican"),("🥩","Steakhouse"),("🍣","Sushi"),("☕","Cafe"),("🍔","Burger")]
    st.caption(tx("home.quick")); qcols=st.columns(3)
    for i,(ico,q) in enumerate(quick):
        with qcols[i%3]:
            if st.button(f"{ico} {translate_cuisine(q,lang())}",key=f"quick_{q}",use_container_width=True): st.session_state.query_food_list=[q]; st.rerun()
    if st.button("🔎 "+tx("home.find"),type="primary",use_container_width=True):
        try:
            with st.spinner(tx("loading.search")):
                locs=geocode(loc_text) if loc_text.strip() else []
                if not locs: st.warning(tx("results.no")); return
                st.session_state.search_location=loc_text
                if len(locs)>1:
                    st.session_state.location_candidates=locs; st.session_state.confirmed_location=None; st.warning(tx("location.choose")); return
                loc=locs[0]; st.session_state.location=loc
                food_values=[x for x in food if x!="All Food Types"]
                st.session_state.query_food_list=food_values
                q=" OR ".join(normalize_cuisine(x) for x in food_values) if food_values else "restaurant"
                results=text_search(f"{q} restaurants near {loc.formatted_address}",loc.latitude,loc.longitude,radius_m=radius*1609.344,max_results=20)
                st.session_state.results=results; st.session_state.radius=radius; st.session_state.sort_mode="Best Overall"; st.rerun()
        except RuntimeError as e:
            if "GOOGLE_MAPS_API_KEY" in str(e): st.error(tx("error.no_key"))
            else: st.error(tx("error.search"))
        except Exception: st.error(tx("error.search"))
    if st.session_state.get("location_candidates"):
        st.markdown(f"### {tx('location.choose')}")
        for i,l in enumerate(st.session_state.location_candidates):
            if st.button(l.formatted_address,key=f"loc_{i}",use_container_width=True): st.session_state.search_location=l.formatted_address; st.session_state.location_candidates=None; st.rerun()
    if st.session_state.results: render_results()


def render_results():
    loc=st.session_state.location; results=st.session_state.results; radius=st.session_state.get("radius",5)
    if not loc:return
    unit="kilometers" if current_profile()["distance_unit"]=="kilometers" or (current_profile()["distance_unit"]=="auto" and loc.country not in (None,"United States")) else "miles"
    st.markdown(f"### 📍 {loc.formatted_address}")
    foods=st.session_state.get("query_food_list",[])
    food_label=", ".join(translate_cuisine(x,lang()) for x in foods) if foods else "All Food Types"
    radius_label=f"{radius} {'km' if unit=='kilometers' else 'mi'}"
    st.caption(f"🍴 {food_label} · {tx('results.within',radius=radius_label)} · {tx('results.found',count=len(results))}")
    top=top_pick_labels(results)
    if top:
        st.markdown(f"#### {tx('results.top')}")
        pickcols=st.columns(min(5,len(top)))
        for i,(label,r) in enumerate(top.items()):
            with pickcols[i%len(pickcols)]:
                st.markdown(f"<div class='rr-card'><div class='rr-badge'>{label}</div><h4>{r.name}</h4><div>⭐ {r.rating or '—'} · {r.review_count:,}</div><div class='rr-score'>{r.rank_score or 0:.2f}</div></div>",unsafe_allow_html=True)
    f1,f2,f3=st.columns([1,1,1])
    with f1: sort=st.selectbox("Sort",[tx(k) for k in ["sort.best","sort.highest","sort.most","sort.combo","sort.gem","sort.value","sort.closest","sort.low","sort.premium"]],index=0)
    sort_map={tx("sort.best"):"Best Overall",tx("sort.highest"):"Highest Rated",tx("sort.most"):"Most Reviewed",tx("sort.combo"):"Best Rated + Most Reviewed",tx("sort.gem"):"Hidden Gems",tx("sort.value"):"Best Value",tx("sort.closest"):"Closest",tx("sort.low"):"Lowest Price",tx("sort.premium"):"Premium"}
    with f2: min_rating=st.selectbox(tx("filter.rating"),[tx("filter.any"),"4.0+","4.5+","4.7+","4.8+","4.9+"])
    with f3: min_reviews=st.selectbox(tx("filter.reviews"),[tx("filter.any"),"25+","50+","100+","500+","1,000+","5,000+"])
    filtered=[r for r in results if (min_rating==tx("filter.any") or (r.rating or 0)>=float(min_rating[:-1])) and (min_reviews==tx("filter.any") or r.review_count>=int(min_reviews.replace(',','')[:-1]))]
    ranked=rank_restaurants(filtered,sort_map.get(sort,"Best Overall"))
    c1,c2=st.columns(2)
    with c1: list_view=st.button("☰ List",use_container_width=True)
    with c2: map_view=st.button("🗺️ Map",use_container_width=True)
    if map_view:
        data=[{"lat":r.latitude,"lon":r.longitude,"name":r.name} for r in ranked if r.latitude is not None and r.longitude is not None]
        if data: st.map(data,zoom=11)
    for idx,r in enumerate(ranked): restaurant_card(r,unit,idx)


def restaurant_card(r,unit,idx):
    photo=None
    if r.photo_url and idx<6:
        try: photo=photo_bytes(r.photo_url)
        except Exception: photo=None
    with st.container():
        st.markdown("<div class='rr-card'>",unsafe_allow_html=True)
        if photo: st.image(photo,use_container_width=True)
        badge="🏆 #1" if idx==0 else f"#{idx+1}"
        st.markdown(f"<div class='rr-badge'>{badge}</div><h3>{r.name}</h3>",unsafe_allow_html=True)
        st.write(f"⭐ {r.rating or '—'} · 💬 {r.review_count:,} · <b>{tx('card.rank')}</b> {r.rank_score or 0:.2f}",unsafe_allow_html=True)
        chips=" ".join(f"<span class='rr-chip'>{translate_cuisine(c,lang())}</span>" for c in r.categories[:3])
        st.markdown(chips+f"<span class='rr-chip'>💵 {r.price_level or '—'}</span><span class='rr-chip'>📍 {format_distance(r.distance_miles,unit)}</span>",unsafe_allow_html=True)
        bcols=st.columns(3)
        with bcols[0]:
            if st.button("❤️ "+tx("card.save"),key=f"save_{r.place_id}",use_container_width=True): save_dialog(r)
        with bcols[1]:
            if st.button("⚖️ "+tx("compare.add"),key=f"cmp_{r.place_id}",use_container_width=True):
                if r.place_id not in [x.place_id for x in st.session_state.compare] and len(st.session_state.compare)<3: st.session_state.compare.append(r)
                st.success("Added to compare")
        with bcols[2]:
            if st.button(tx("card.details"),key=f"details_{r.place_id}",use_container_width=True): details_dialog(r)
        st.markdown("</div>",unsafe_allow_html=True)


def save_dialog(r):
    cols=collections(st.session_state.profile_id)
    st.session_state.save_target=r
    choices=[c["name"] for c in cols]
    selected=st.multiselect(tx("favorites.select"),choices,key=f"favlists_{r.place_id}")
    if st.button(tx("favorites.save"),key=f"favs_{r.place_id}"):
        payload=r.__dict__.copy(); payload["cuisine_labels"]=r.cuisine_labels; payload["snapshot_note"]="Saved information"
        existing={c["name"]:c["id"] for c in cols}
        for name in selected: save_favorite(st.session_state.profile_id,existing[name],r.place_id,payload)
        st.success("Saved!")


def details_dialog(r):
    d=r
    try:
        with st.spinner(tx("loading.details")): d=get_place_details(r.place_id)
    except Exception: pass
    st.markdown(f"### {d.name}")
    cols=st.columns(2)
    with cols[0]: st.write(f"⭐ {d.rating or '—'} · 💬 {d.review_count:,}"); st.write(f"**{tx('card.rank')}:** {r.rank_score or 0:.2f}"); st.write(d.address)
    with cols[1]:
        st.write(d.opening_status or tx("card.unknown"));
        if d.phone: st.write(f"📞 {d.phone}")
        if d.website: st.link_button("🌐 Website",d.website)
        if d.maps_url: st.link_button("🗺️ Google Maps",d.maps_url)
    if d.opening_hours:
        with st.expander("Hours"): st.write("\n".join(d.opening_hours))
    st.info("Dish-level recommendations aren't available from the current data source. Check the restaurant's current menu for specialties.")


def favorites_page():
    header(); st.subheader(tx("favorites.title"))
    cols=collections(st.session_state.profile_id)
    if st.button("＋ "+tx("favorites.new"),use_container_width=True): st.session_state.show_new_collection=True
    if st.session_state.get("show_new_collection"):
        name=st.text_input("List name",key="new_list_name");
        if st.button("Create list"):
            try:create_collection(st.session_state.profile_id,clean_collection_name(name)); st.session_state.show_new_collection=False; st.rerun()
            except Exception as e: st.error(str(e))
    if not cols: st.info(tx("favorites.empty")); return
    names=[c["name"] for c in cols]; chosen=st.selectbox(tx("favorites.select"),names)
    cid=next(c["id"] for c in cols if c["name"]==chosen)
    rows=favorite_rows(st.session_state.profile_id,cid)
    if not rows: st.info(tx("favorites.empty")); return
    for row in rows:
        p=row; r=json.loads(p["payload"])
        st.markdown(f"<div class='rr-card'><h3>{r.get('name','Restaurant')}</h3><div>⭐ {r.get('rating') or '—'} · 💬 {r.get('review_count',0):,} · {r.get('cuisine_labels') or r.get('categories') or ''}</div><div class='rr-muted'>{r.get('address','')}</div><div class='rr-muted'>Saved information from {p['saved_at'][:10]}</div></div>",unsafe_allow_html=True)
        if st.button(tx("favorites.remove"),key=f"rm_{cid}_{r.get('place_id')}"): remove_favorite(st.session_state.profile_id,cid,r.get('place_id')); st.rerun()


def compare_page():
    header(); st.subheader(tx("compare.title"))
    if not st.session_state.compare: st.info(tx("compare.empty")); return
    if st.button(tx("compare.clear")): st.session_state.compare=[]; st.rerun()
    cols=st.columns(len(st.session_state.compare))
    for i,r in enumerate(st.session_state.compare):
        with cols[i]:
            st.markdown(f"<div class='rr-card'><h3>{r.name}</h3><div>⭐ {r.rating or '—'}</div><div>💬 {r.review_count:,}</div><div class='rr-score'>{r.rank_score or 0:.2f}</div><div>{r.categories[:2]}</div><div>{r.price_level or '—'}</div><div>{format_distance(r.distance_miles,'miles')}</div></div>",unsafe_allow_html=True)
            if st.button("Remove",key=f"rcomp_{r.place_id}"): st.session_state.compare.pop(i); st.rerun()


def profile_page():
    header(); p=current_profile()
    st.subheader(f"👤 {p['name']}")
    tabs=st.tabs([tx("settings.language"),tx("settings.theme"),tx("settings.appearance"),tx("settings.backup")])
    with tabs[0]:
        language=st.selectbox(tx("settings.language"),["English","Español"],index=0 if p["language"]=="en" else 1)
        units=st.selectbox(tx("settings.units"),["auto","miles","kilometers"],index=["auto","miles","kilometers"].index(p["distance_unit"]))
        radius=st.selectbox(tx("settings.radius"),[1,3,5,10,15,25],index=[1,3,5,10,15,25].index(p["default_radius"]))
        if st.button("Save language & units"):
            update_settings(p["id"],language="en" if language=="English" else "es",distance_unit=units,default_radius=radius); st.rerun()
    with tabs[1]:
        theme=st.selectbox(tx("settings.theme"),list(THEMES.keys()),index=list(THEMES.keys()).index(p["theme"]),format_func=lambda x:tx(f"theme.{x}"))
        if st.button("Save theme"): update_settings(p["id"],theme=theme); st.rerun()
    with tabs[2]:
        appearance=st.selectbox(tx("settings.appearance"),["light","dark","system"],index=["light","dark","system"].index(p["appearance"]),format_func=lambda x:tx(f"appearance.{x}"))
        if st.button("Save appearance"): update_settings(p["id"],appearance=appearance); st.rerun()
    with tabs[3]:
        data=export_backup(p["id"])
        st.download_button(tx("settings.download"),json.dumps(data,ensure_ascii=False,indent=2),file_name="restaurant_rank_backup.json",mime="application/json")
        uploaded=st.file_uploader(tx("settings.restore"),type=["json"])
        mode=st.radio(tx("settings.mode"),[tx("settings.merge"),tx("settings.replace")])
        if uploaded and st.button(tx("settings.restore")):
            try: obj=validate_backup_bytes(uploaded.getvalue()); import_backup(p["id"],obj,"replace" if mode==tx("settings.replace") else "merge"); st.success(tx("backup.restored")); st.rerun()
            except Exception as e: st.error(str(e))
    st.divider()
    with st.expander(tx("profile.change_pin")):
        current=st.text_input(tx("profile.current_pin"),type="password",max_chars=4)
        new=st.text_input(tx("profile.new_pin"),type="password",max_chars=4)
        confirm=st.text_input(tx("profile.confirm_pin"),type="password",max_chars=4)
        if st.button(tx("profile.change_pin")):
            if authenticate_pin(p["id"],current)[0] and valid_pin(new) and new==confirm: change_pin(p["id"],new); st.success(tx("security.pin_ok"))
            else: st.error(tx("security.wrong"))
    with st.expander(tx("settings.about")): st.write(tx("about.text")); st.write("RestaurantRank Score uses a Bayesian-style confidence adjustment and is not a Google rating.")
    with st.expander(tx("settings.how")): st.write("Best Overall uses a Bayesian-style rating: (v/(v+m))*R + (m/(v+m))*C, with m=50 by default. Other modes add review confidence, price, or distance as documented in the ranking engine.")
    with st.expander(tx("settings.privacy")): st.write("RestaurantRank does not require a traditional email/password account. PINs are hashed, recovery codes are hashed, and backups exclude secrets, PINs, recovery codes, and API keys. Storage persistence depends on the configured deployment filesystem; download backups for portable recovery.")
    st.divider()
    c1,c2=st.columns(2)
    with c1:
        if st.button(tx("nav.logout"),use_container_width=True): st.session_state.profile_id=None; st.session_state.unlocked=False; st.session_state.page="search"; st.rerun()
    with c2:
        if st.button(tx("profile.delete"),use_container_width=True): st.session_state.confirm_delete=True
    if st.session_state.get("confirm_delete"):
        st.warning(tx("profile.delete_warn"))
        if st.button("Delete permanently",type="primary"): delete_profile(p["id"]); st.session_state.profile_id=None; st.session_state.unlocked=False; st.session_state.confirm_delete=False; st.rerun()


def main():
    if not st.session_state.unlocked or not st.session_state.profile_id:
        profile_gate(); return
    nav()
    page=st.session_state.page
    if page=="search": search_page()
    elif page=="favorites": favorites_page()
    elif page=="compare": compare_page()
    else: profile_page()
    st.caption("Restaurant data and ratings shown here are sourced from Google Places where available. RestaurantRank Score is calculated by RestaurantRank.")

main()
