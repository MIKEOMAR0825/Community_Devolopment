from alembic.util import status
from flask import ( Flask, render_template, request, redirect, url_for, flash, session )

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from extensions import (
    db,
    migrate,
    mail
)

from models import (
    Subscriber,
    ContactMessage,
    Donation
)

from flask_mail import Message
import json
import os
from config import Config

from pathlib import Path
from deep_translator import GoogleTranslator
from texts import TEXTS

from deep_translator import (
    GoogleTranslator
)

from requests.exceptions import (
    ConnectionError,
    Timeout
)

import logging

import requests
import uuid
from flask import jsonify

import hmac
import hashlib
import os



logging.basicConfig(level=logging.ERROR)


app = Flask(__name__)

#===============================================
# CONFIGURATION
#===============================================
app.config.from_object(Config)

#================================
# INITIALISATION EXTENSIONS
#================================
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)


# ------------ LANGUES --------------------
LANGUAGES = {
    'fr': 'Français',
    'en': 'English',
    'es': 'Español',
    'sw': 'Kiswahili',
    'zh-CN': '中文 (Mandarin)'
}


#TRANSLATION_FILE = Path("translations.json")

# ----------------- Cache -----------------
#if TRANSLATION_FILE.exists():
#    with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
#        translation_cache = json.load(f)
#else:
#    translation_cache = {}


#def save_translations():
#    with open(TRANSLATION_FILE, "w", encoding="utf-8") as f:
#        json.dump(translation_cache, f, ensure_ascii=False, indent=4)


TRANSLATIONS_DIR = Path("translations")
TRANSLATIONS_DIR.mkdir(exist_ok=True)

def load_language_file(lang):
    file_path = TRANSLATIONS_DIR / f"{lang}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {}

def save_language_file(lang, data):
    file_path = TRANSLATIONS_DIR / f"{lang}.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


#=========== AVANT =======================================        
#def translate_value(value, lang):
#    if isinstance(value, str):
#        return GoogleTranslator(source='fr', target=lang).translate(value)
    
#    elif isinstance(value, list):
#        return [translate_value(v, lang) for v in value]
#    
#    elif isinstance(value, dict):
#        return {k: translate_value(v, lang) for k, v in value.items()}
    
#    return value

# =========== APRES =====================================
def translate_value(value, lang):

    try:

        if isinstance(value, str):

            return (
                GoogleTranslator(
                    source="fr",
                    target=lang
                )
                .translate(value)
            )

        elif isinstance(value, list):

            return [
                translate_value(v, lang)
                for v in value
            ]

        if isinstance(value, dict):

            result = {}

            translator = GoogleTranslator(
                source="fr",
                target=lang
            )

            for k, v in value.items():

                translated_key = (
                    translator.translate(k)
                    if isinstance(k, str)
                    else k
                )

                result[translated_key] = (
                    translate_value(v, lang)
                )

            return result


    except (
        ConnectionError,
        Timeout,
        Exception
    ) as e:

        logging.exception(
            f"Erreur traduction : {e}"
        )

        # Fallback :
        return value


def get_lang():
    return session.get('lang', 'fr')

# ----------------- Traduction automatique -----------------
def translate_texts(page_name, lang):
    page_texts = TEXTS.get(page_name, {})

    if lang == "fr":
        return page_texts

    lang_data = load_language_file(lang)

    if page_name not in lang_data:
        lang_data[page_name] = {}

    translated = {}
    changed = False

    for key, value in page_texts.items():

        cached = lang_data[page_name].get(key)

        # 🔥 CAS 1 : pas encore traduit
        if not cached:
            translated_text = translate_value(value, lang)

            lang_data[page_name][key] = {
                "source": value,
                "translated": translated_text
            }

            translated[key] = translated_text
            changed = True

        # 🔥 CAS 2 : source a changé → retraduire
        elif cached["source"] != value:
            translated_text = translate_value(value, lang)

            lang_data[page_name][key] = {
                "source": value,
                "translated": translated_text
            }

            translated[key] = translated_text
            changed = True

        # 🔥 CAS 3 : déjà OK
        else:
            translated[key] = cached["translated"]

    if changed:
        save_language_file(lang, lang_data)

    return translated

# ----------------- Hook pour traduire toutes les pages -----------------

# ========== AVANT ==========================
#@app.before_request
#def auto_translate_request():
#    endpoint = request.endpoint
#    if not endpoint:
#        return
#    page_name = endpoint
#    request.translated_texts = translate_texts(page_name, get_lang())
#    request.current_lang = get_lang()

# ========= APRES ==============================
@app.before_request
def auto_translate_request():

    try:

        endpoint = request.endpoint

        if not endpoint:
            return

        request.translated_texts = (
            translate_texts(
                endpoint,
                get_lang()
            )
        )

        request.current_lang = get_lang()

    except Exception as e:

        print("TRANSLATION ERROR:", e)

        request.translated_texts = (
            TEXTS.get(
                request.endpoint,
                {}
            )
        )

        request.current_lang = "fr"

# ----------------- ROUTES -----------------   

@app.route('/base')
def base():
    render_template('base.html',texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES ) 

@app.route('/')
def accueil():
    return render_template('index.html', texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/mission")
def mission():
    return render_template("mission.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/apropos")
def apropos():
    return render_template("apropos.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/actualite")
def actualite():
    return render_template("actualite.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/project")
def project():
    return render_template("projet.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/donation")
def donation():
    return render_template("donation.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)
    
    
    

@app.route("/soutien")
def soutien():
    return render_template("soutien.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/benevolat")
def benevolat():
    return render_template("benevolat.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

@app.route("/login")
def login():
    return render_template("login.html", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)

# -----------------------------
# CONTACT
# -----------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        service = request.form.get("service")
        message_text = request.form.get("message")

        # -----------------------------
        # SAVE DATABASE
        # -----------------------------
        new_message = ContactMessage(
            full_name=full_name,
            email=email,
            phone=phone,
            service=service,
            message=message_text
        )

        db.session.add(new_message)
        db.session.commit()

        # -----------------------------
        # EMAILS
        # -----------------------------
        company_email = Message(
            subject="Nouveau message client",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]]
        )

        company_email.html = f"""
            <h2>Nouveau message reçu</h2>
            <p><strong>Nom :</strong> {full_name}</p>
            <p><strong>Email :</strong> {email}</p>
            <p><strong>Téléphone :</strong> {phone}</p>
            <p><strong>Service :</strong> {service}</p>
            <p><strong>Message :</strong></p>
            <p>{message_text}</p>
        """

        user_email = Message(
            subject="Nous avons bien reçu votre message",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        user_email.html = f"""
            <h2>Bonjour {full_name} 👋</h2>

            <p>Merci de nous avoir contactés.</p>

            <p>
                Notre équipe analysera votre demande
                et vous répondra rapidement.
            </p>

            <br>

            <p>
                Cordialement,<br>
                COMMUNITY DEVELOPMENT 
            </p>
        """

        # -----------------------------
        # SAFE EMAIL SENDING
        # -----------------------------
        try:
            mail.send(company_email)
            mail.send(user_email)

            flash("Votre message a été envoyé avec succès.", "success")

        except Exception as e:
            print("MAIL ERROR (contact):", e)
            flash("Message enregistré, mais email non envoyé.", "warning")

        return redirect(url_for("contact"))

    return render_template("contact.html", titre="Contact", texts=request.translated_texts,
                           lang=request.current_lang, LANGUAGES=LANGUAGES)




# ----------------- NEWSLETTER -----------------
@app.route( "/newsletter", methods=["POST"])
def newsletter():

    email = request.form.get("email")

    if not email:
        flash("Veuillez entrer une adresse valide","error")
        return redirect(url_for("accueil"))

    exists = Subscriber.query.filter_by(email=email).first()

    if exists:
        flash("Cette adresse existe déjà.","warning")
        return redirect(url_for("accueil"))

    try:
        new_subscriber = Subscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()

        # -----------------------------
        # SEND EMAIL
        # -----------------------------
        msg = Message(
            subject="Merci pour votre inscription",
            recipients=[email]
        )

        msg.html = """
            <h2>Bienvenue 🎉</h2>

            <p>
                Merci de vous être inscrit à notre newsletter.
            </p>

            <p>
            Nous sommes ravis de vous compter parmi nos abonnés.
            Vous recevrez desormais les dernières nouvelles, 
            offres et mises à jour directement dans votre boîte de réception.
            </p>
            
            <p>
                Merci pour votre confiance.
            </p>
            
            <br>

            <p>
                Cordialement,<br>
                Community Development
            </p>
        """

        try:
            mail.send(msg)

        except Exception as e:
            print("MAIL SEND ERROR:", e)

        flash(
            "Inscription enregistrée avec succès.",
            "success"
        )

    except Exception as e:
        db.session.rollback()

        print("NEWSLETTER ERROR:", str(e))

        flash(
            f"Erreur : {str(e)}",
            "error"
        )
        
    return redirect(url_for("accueil"))
    



# ----------------- ADMIN NEWSLETTER -----------------
@app.route("/admin")
def admin():

    subscribers = ( Subscriber.query.order_by(
            Subscriber.created_at.desc() ) .all())

    return render_template( "admin.html", 
                           subscribers=subscribers, texts=request.translated_texts, 
                           lang=request.current_lang, LANGUAGES=LANGUAGES)
    

#===============================================
# SUPPRIMER ABONNÉ
#===============================================
@app.route("/admin/delete/<int:id>")
def delete_subscriber(id):

    subscriber = Subscriber.query.get_or_404(id)

    db.session.delete(subscriber)

    db.session.commit()

    flash("Abonné supprimé.","success")

    return redirect(url_for("admin"))
    

#==========================================
# ENVOYER NEWSLETTER
#==========================================
@app.route("/admin/send", methods=["POST"])
def send_newsletter():

    subject = request.form.get("subject")
    content = request.form.get("content")

    if not subject or not content:
        flash("Remplissez tous les champs", "error")
        return redirect(url_for("admin"))

    subscribers = Subscriber.query.all()

    for sub in subscribers:
        try:
            msg = Message(
                subject=subject,
                sender=app.config["MAIL_USERNAME"],
                recipients=[sub.email]
            )
            msg.html = content

            mail.send(msg)

        except Exception as e:
            print(f"Erreur → {e}")

    flash("Newsletter envoyée ✅", "success")
    return redirect(url_for("admin"))


# ----------------- CHANGEMENT DE LANGUE -----------------
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in LANGUAGES:
        session['lang'] = lang
    return redirect(request.referrer)


#=====================================================
#   PAIEMENT EN LIGNE
#=====================================================
@app.route("/create-donation", methods=["POST"])
def create_donation():

    transaction_id = str(uuid.uuid4())

    name = request.form.get("name")
    email = request.form.get("email")
    amount = float(request.form.get("amount"))
    phone = request.form.get("phone")
    method = request.form.get("payment_method")

    # 1. Save DB
    donation = Donation(
        transaction_id=transaction_id,
        donor_name=name,
        email=email,
        amount=amount,
        payment_method=method,
        status="pending"
    )

    db.session.add(donation)
    db.session.commit()

    # 2. CALL PAYMENT API (RDC mobile money)
    payload = {
        "amount": amount,
        "currency": "USD" if method == "card" else "USD",
        "phone": phone,
        "reference": transaction_id,
        "callback_url": url_for("webhook", _external=True)
    }

    headers = {
        "Authorization": f"Bearer {app.config['PAYMENT_API_KEY']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            app.config["PAYMENT_API_URL"],
            json=payload,
            headers=headers,
            timeout=30
        )

        result = response.json()

        # 3. Si API OK
        status = result.get("status")

        if status in ["PENDING", "WAITING", "PROCESSING"]:  

            flash("Demande de paiement envoyée sur votre téléphone", "success")

            return redirect(url_for("success_payment"))

        else:
            flash("Erreur de paiement", "error")
            return redirect(url_for("donation"))

    except Exception as e:
        print("PAYMENT ERROR:", e)
        flash("Erreur serveur paiement", "error")
        return redirect(url_for("donation"))
        
    
@app.route(
"/success-payment"
)
def success_payment():

    return """
    <h1>
    Paiement créé ✅
    </h1>
    """
    


import hmac
import hashlib
import os


@app.route("/webhook", methods=["POST"])
def webhook():

    signature = request.headers.get("X-Signature", "")

    secret = app.config["WEBHOOK_SECRET"]

    expected = hmac.new(
        secret.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()

    if signature != expected:
        return {"error": "invalid signature"}, 403

    payload = request.json

    transaction_id = payload.get("transaction_id")
    status = payload.get("status")

    donation = Donation.query.filter_by(transaction_id=transaction_id).first()

    if not donation:
        return {"error": "not found"}, 404

    if status == "SUCCESS":
        donation.status = "paid"
    else:
        donation.status = "failed"

    db.session.commit()

    return {"ok": True}, 200

    
            

# ----------------- MAIN -----------------
if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
