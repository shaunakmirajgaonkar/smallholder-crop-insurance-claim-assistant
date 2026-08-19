from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CropClaim Local",page_icon="🌾",layout="wide")
DATA=Path("data/crop_insurance_claim_registry.csv")
REQ=['claim_id', 'farmer_record_code', 'crop_type', 'village', 'damage_date', 'report_date', 'area_affected_acres', 'damage_percent', 'cause_category', 'crop_stage', 'policy_reference_present', 'land_record_present', 'sowing_evidence_present', 'damage_photo_count', 'field_report_present', 'weather_evidence_present', 'harvest_estimate_present', 'notice_within_window', 'insurer_acknowledged', 'insurer_response_days', 'follow_up_status', 'review_status']

st.markdown("""
<style>
.stApp{background:#f6f8f6;color:#17231b}.block-container{max-width:1500px;padding:1.2rem 2rem 3rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #dfe7e1}
.hero{background:linear-gradient(135deg,#fff,#f0f8f2);border:1px solid #d8e5dc;border-radius:26px;padding:30px;margin-bottom:20px}
.hero h1{color:#142219;font-size:2.35rem}.hero p{color:#536259;line-height:1.6}
.badge{display:inline-block;padding:7px 11px;margin-right:6px;border-radius:999px;background:#edf7ef;border:1px solid #d3e7d8;color:#27613a;font-size:11px;font-weight:800}
div[data-testid="stMetric"]{background:#fff;border:1px solid #dfe7e1;border-radius:16px;padding:14px}
</style>
""",unsafe_allow_html=True)

def yes(v): return str(v).lower().strip() in {"true","yes","1","y"}
def num(v):
    try:return float(v)
    except:return 0.0

def score(r):
    s=0; reasons=[]
    if num(r.damage_percent)>=75:s+=20;reasons.append("High reported damage level.")
    elif num(r.damage_percent)>=40:s+=14;reasons.append("Material reported damage level.")
    elif num(r.damage_percent)>0:s+=7;reasons.append("Reported damage is present.")
    pts={"policy_reference_present":8,"land_record_present":8,"sowing_evidence_present":7,"field_report_present":10,"weather_evidence_present":7,"harvest_estimate_present":6,"notice_within_window":12}
    for c,p in pts.items():
        if yes(r[c]):s+=p
        else:reasons.append(c.replace("_"," ").title()+" not confirmed.")
    photos=num(r.damage_photo_count)
    if photos>=5:s+=8;reasons.append("Multiple damage photographs recorded.")
    elif photos>=2:s+=5;reasons.append("Some damage photographs recorded.")
    else:reasons.append("Limited photographic evidence.")
    if yes(r.insurer_acknowledged):s+=4
    else:reasons.append("Insurer acknowledgement not recorded.")
    if num(r.insurer_response_days)>14:s+=5;reasons.append("Extended insurer response interval.")
    label="Complete" if s>=80 else "Mostly Complete" if s>=60 else "Needs Evidence" if s>=40 else "Early Review"
    return min(s,100),label,reasons

try:
    df=pd.read_csv(DATA)
    missing=[c for c in REQ if c not in df.columns]
    if missing: raise ValueError("Missing required columns: "+", ".join(missing))
except Exception:
    df=pd.DataFrame(columns=REQ)

if not df.empty:
    x=df.apply(score,axis=1,result_type="expand")
    x.columns=["completeness_score","completeness_class","reasons"]
    df=pd.concat([df.reset_index(drop=True),x],axis=1)

st.sidebar.markdown("## 🌾 CropClaim Local")
st.sidebar.caption("Smallholder crop-insurance claim support")
page=st.sidebar.radio("Workspace",["Command Center","Claim Review","Evidence Audit","Claims Analytics","Local Data Lab","Responsible Use"])

st.markdown("""
<div class="hero">
<span class="badge">LOCAL-FIRST</span><span class="badge">EVIDENCE-AWARE</span><span class="badge">EXPLAINABLE</span><span class="badge">HUMAN REVIEW</span>
<h1>🌾 CropClaim Local</h1>
<p><b>Smallholder Crop Insurance Claim Assistant</b> — organize crop-damage evidence, screen administrative completeness, and track insurer-response signals.</p>
<p>Scores do not determine coverage, claim validity, compensation, eligibility, fraud, or insurer responsibility.</p>
</div>
""",unsafe_allow_html=True)

if page=="Command Center":
    if df.empty: st.warning("Load a valid claim registry in Local Data Lab.")
    else:
        a,b,c,d,e=st.columns(5)
        a.metric("Claims screened",len(df));b.metric("Needs evidence",int((df.completeness_score<60).sum()));c.metric("Strong evidence",int((df.completeness_score>=80).sum()));d.metric("Acknowledged",int(df.insurer_acknowledged.apply(yes).sum()));e.metric("Avg response days",f"{df.insurer_response_days.apply(num).mean():.1f}")
        q=df.completeness_class.value_counts().reset_index();q.columns=["class","count"]
        fig=px.bar(q,x="class",y="count",title="Evidence-completeness distribution");fig.update_layout(template="plotly_white",height=380);st.plotly_chart(fig,use_container_width=True)
        cols=["claim_id","farmer_record_code","crop_type","village","damage_percent","completeness_score","completeness_class","follow_up_status"]
        st.dataframe(df.sort_values("completeness_score")[cols],use_container_width=True,hide_index=True)

elif page=="Claim Review":
    if df.empty: st.info("Load a registry first.")
    else:
        selected=st.selectbox("Claim",df.claim_id.astype(str));r=df[df.claim_id.astype(str)==selected].iloc[0]
        a,b,c,d=st.columns(4);a.metric("Completeness",f"{r.completeness_score:.0f}/100");b.metric("Class",r.completeness_class);c.metric("Damage",f"{num(r.damage_percent):.0f}%");d.metric("Photos",f"{num(r.damage_photo_count):.0f}")
        st.write(f"**Crop:** {r.crop_type}  |  **Village:** {r.village}  |  **Affected area:** {num(r.area_affected_acres):.2f} acres  |  **Cause:** {r.cause_category}")
        st.write(f"**Follow-up:** {r.follow_up_status}  |  **Insurer response:** {num(r.insurer_response_days):.0f} days")
        for reason in r.reasons: st.write("• "+reason)

elif page=="Evidence Audit":
    if df.empty: st.info("Load a registry first.")
    else:
        cols=["policy_reference_present","land_record_present","sowing_evidence_present","field_report_present","weather_evidence_present","harvest_estimate_present","notice_within_window"]
        audit=pd.DataFrame({"evidence_item":[c.replace("_"," ").title() for c in cols],"missing_or_unconfirmed":[int((~df[c].apply(yes)).sum()) for c in cols]})
        fig=px.bar(audit,x="evidence_item",y="missing_or_unconfirmed",title="Missing or unconfirmed evidence");fig.update_layout(template="plotly_white",height=420);st.plotly_chart(fig,use_container_width=True)
        st.dataframe(audit,use_container_width=True,hide_index=True)

elif page=="Claims Analytics":
    if df.empty: st.info("Load a registry first.")
    else:
        fig=px.scatter(df,x="damage_percent",y="completeness_score",size="area_affected_acres",color="crop_type",hover_name="claim_id",title="Damage vs evidence completeness")
        fig.update_layout(template="plotly_white",height=430);st.plotly_chart(fig,use_container_width=True)

elif page=="Local Data Lab":
    st.write("CSV files are processed locally and validated before replacement.")
    st.code(", ".join(REQ))
    up=st.file_uploader("Replace local crop-insurance claim registry",type=["csv"])
    if up:
        try:
            nd=pd.read_csv(up);missing=[c for c in REQ if c not in nd.columns]
            if missing: st.error("Missing required columns: "+", ".join(missing))
            else: nd.to_csv(DATA,index=False);st.success(f"Loaded {len(nd):,} claim records.");st.rerun()
        except Exception as e: st.error(str(e))
    if not df.empty:
        st.dataframe(df[REQ],use_container_width=True,hide_index=True)
        st.download_button("Download scored claim registry",df.drop(columns=["reasons"]).to_csv(index=False).encode(),"crop_insurance_scored_claim_registry.csv","text/csv")

else:
    st.write("CropClaim Local is administrative decision support only. It does not determine coverage, claim validity, compensation, eligibility, fraud, loss valuation, or insurer liability. Use synthetic or authorized records, minimize personal information, preserve original evidence, and verify requirements against the applicable policy and insurer process.")

st.markdown("---")
st.caption("CropClaim Local • 100% local processing • No external APIs • Crop-insurance claim decision support")
