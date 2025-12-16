from flask import Flask, jsonify, request
from flask_cors import CORS
import io
import csv
from flask import Response

app = Flask(__name__)
CORS(app)  # allow calls from your frontend (localhost:3000, etc.)

# ---------- Mock data ----------
leads = [
    {
        "id": 1,
        "name": "Alice Johnson",
        "title": "Director of Toxicology",
        "company": "LiverTech Biotherapeutics",
        "person_location": "Remote - Denver, CO",
        "hq_location": "Cambridge, MA",
        "email": "alice.johnson@livertechbio.com",
        "company_funding_stage": "Series B",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": True,
    },
    {
        "id": 2,
        "name": "Bob Smith",
        "title": "Senior Scientist, Investigative Toxicology",
        "company": "NeoPharma Labs",
        "person_location": "Boston, MA",
        "hq_location": "Boston, MA",
        "email": "bob.smith@neopharmalabs.com",
        "company_funding_stage": "Series A",
        "uses_in_vitro_models": True,
        "open_to_nams": False,
        "in_hub": True,
        "published_dili_paper_last_2y": False,
    },
    {
        "id": 3,
        "name": "Carla Ruiz",
        "title": "Junior Scientist, In Vivo Pharmacology",
        "company": "StartX Bio",
        "person_location": "Austin, TX",
        "hq_location": "Austin, TX",
        "email": "carla.ruiz@startxbio.com",
        "company_funding_stage": "Pre-seed",
        "uses_in_vitro_models": False,
        "open_to_nams": False,
        "in_hub": False,
        "published_dili_paper_last_2y": False,
    },
    {
        "id": 4,
        "name": "David Lee",
        "title": "Head of Preclinical Safety",
        "company": "BayArea Therapeutics",
        "person_location": "Remote - Seattle, WA",
        "hq_location": "South San Francisco, CA",
        "email": "david.lee@bayareatherapeutics.com",
        "company_funding_stage": "Series C",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": True,
    },
    {
        "id": 5,
        "name": "Emma Watson",
        "title": "Associate Director, Hepatic Safety",
        "company": "Basel BioSystems",
        "person_location": "Basel, Switzerland",
        "hq_location": "Basel, Switzerland",
        "email": "emma.watson@baselbiosystems.com",
        "company_funding_stage": "Series B",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": False,
    },
    {
        "id": 6,
        "name": "Frank Müller",
        "title": "VP Preclinical Development",
        "company": "Golden Triangle Pharma",
        "person_location": "Oxford, UK",
        "hq_location": "Cambridge, UK",
        "email": "frank.muller@goldentrianglepharma.com",
        "company_funding_stage": "Series A",
        "uses_in_vitro_models": False,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": True,
    },
    {
        "id": 7,
        "name": "Grace Kim",
        "title": "Principal Scientist, 3D Cell Culture",
        "company": "OrganoChip Therapeutics",
        "person_location": "San Francisco, CA",
        "hq_location": "South San Francisco, CA",
        "email": "grace.kim@organochip.com",
        "company_funding_stage": "Series B",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": True,
    },
    {
        "id": 8,
        "name": "Henry Brown",
        "title": "Research Scientist, Liver Toxicity",
        "company": "Hepato3D Solutions",
        "person_location": "Remote - Raleigh, NC",
        "hq_location": "Boston, MA",
        "email": "henry.brown@hepato3d.com",
        "company_funding_stage": "Seed",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": False,
    },
    {
        "id": 9,
        "name": "Isabel Garcia",
        "title": "Senior Toxicologist",
        "company": "NeoPharma Labs",
        "person_location": "Madrid, Spain",
        "hq_location": "Berlin, Germany",
        "email": "isabel.garcia@neopharmalabs.com",
        "company_funding_stage": "Series C",
        "uses_in_vitro_models": False,
        "open_to_nams": False,
        "in_hub": False,
        "published_dili_paper_last_2y": True,
    },
    {
        "id": 10,
        "name": "John Patel",
        "title": "Director of Safety Assessment",
        "company": "LiverTech Biotherapeutics",
        "person_location": "Cambridge, MA",
        "hq_location": "Cambridge, MA",
        "email": "john.patel@livertechbio.com",
        "company_funding_stage": "Series B",
        "uses_in_vitro_models": True,
        "open_to_nams": True,
        "in_hub": True,
        "published_dili_paper_last_2y": True,
    },
]

# ---------- Scoring ----------
def compute_score(lead):
    score = 0
    title = lead["title"].lower()

    # role fit
    if any(k in title for k in ["toxicology", "safety", "hepatic", "3d"]):
        score += 30
    # funding
    funding = lead["company_funding_stage"].lower()
    if "series a" in funding or "series b" in funding or "series c" in funding:
        score += 20
    # technographic
    if lead.get("uses_in_vitro_models"):
        score += 15
    if lead.get("open_to_nams"):
        score += 10
    # location hub
    if lead.get("in_hub"):
        score += 10
    # scientific intent
    if lead.get("published_dili_paper_last_2y"):
        score += 40

    return min(score, 100)

def get_ranked_leads(query=None, min_score=0):
    enriched = []
    for lead in leads:
        s = compute_score(lead)
        if s < min_score:
            continue

        # free-text filter
        if query:
            q = query.lower()
            text = " ".join(
                [
                    lead["name"],
                    lead["title"],
                    lead["company"],
                    lead["person_location"],
                    lead["hq_location"],
                ]
            ).lower()
            if q not in text:
                continue

        enriched.append({**lead, "probability_score": s})

    enriched.sort(key=lambda x: x["probability_score"], reverse=True)
    for i, lead in enumerate(enriched, start=1):
        lead["rank"] = i
    return enriched

# ---------- API routes ----------
@app.route("/api/leads", methods=["GET"])
def list_leads():
    query = request.args.get("q", "").strip() or None
    min_score = int(request.args.get("min_score", "0"))
    data = get_ranked_leads(query=query, min_score=min_score)
    return jsonify({"leads": data})
@app.route("/api/leads/csv", methods=["GET"])
def download_leads_csv():
    query = request.args.get("q", "").strip() or None
    min_score = int(request.args.get("min_score", "0"))
    data = get_ranked_leads(query=query, min_score=min_score)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank",
        "Score",
        "Name",
        "Title",
        "Company",
        "Person Location",
        "Company HQ",
        "Email"
    ])

    for l in data:
        writer.writerow([
            l["rank"],
            l["probability_score"],
            l["name"],
            l["title"],
            l["company"],
            l["person_location"],
            l["hq_location"],
            l["email"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ranked_leads.csv"}
    )
if __name__ == "__main__":
    app.run(debug=True)
