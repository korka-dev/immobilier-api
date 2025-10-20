from passlib.context import CryptContext
import os
from datetime import datetime
from app.models.user import User
import httpx
from dotenv import load_dotenv
load_dotenv()

SENDINBLUE_API_KEY = os.getenv("SENDINBLUE_API_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashed(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)

    return f"{base}_{datetime.utcnow()}{ext}"


def authenticate_user(username: str, password: str):
    user = User.objects(username=username).first()

    if user is None:
        return None  

    if not verify(password, user.password):
        return None  

    return user 


async def send_user_request_email(name: str, email: str, agence: str, contact: str):
    url = "https://api.brevo.com/v3/smtp/email"
    subject = "📩 Nouvelle demande de compte utilisateur Sunu-Villa"
    html_content = f"""
    <div>
      <h2>📩 Nouvelle demande de compte utilisateur Sunu-Villa</h2>
      <p><strong>Nom :</strong> {name}</p>
      <p><strong>Email :</strong> {email}</p>
      <p><strong>Agence :</strong> {agence}</p>
      <p><strong>Contact :</strong> {contact}</p>
    </div>
    """
    data = {
        "sender": {"name": "Sunu-Villa Support", "email": "diallo30amadoukorka@gmail.com"}, 
        "to": [{"email": "diallo30amadoukorka@gmail.com"}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {
        "api-key": SENDINBLUE_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def send_account_created_email(client_email: str, client_name: str, password: str):
    """
    Envoie un email au client avec une mise en page améliorée
    """
    url = "https://api.brevo.com/v3/smtp/email"
    subject = "✅ Votre compte sur Sunu-Villa est prêt !"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #0d6efd;">Bonjour {client_name},</h2>
        <p>Nous avons le plaisir de vous informer que votre compte sur <strong>Sunu-Villa</strong> a été créé avec succès !</p>

        <div style="background-color: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #0d6efd;">Vos identifiants :</h3>
            <ul style="list-style: none; padding-left: 0;">
                <li><strong>Email :</strong> {client_email}</li>
                <li><strong>Mot de passe :</strong> {password}</li>
            </ul>
        </div>

        <p>Nous vous recommandons de <strong>changer votre mot de passe</strong> dès votre première connexion pour plus de sécurité.</p>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="https://sunu-villa.vercel.app/login" style="background-color: #0d6efd; color: #fff; text-decoration: none; padding: 12px 25px; border-radius: 5px;">Se connecter à Sunu-Villa</a>
        </p>

        <p>Cordialement,<br/>
        L'équipe <strong>Sunu-Villa Support</strong></p>

        <hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
        <p style="font-size: 12px; color: #888;">Si vous n'avez pas demandé la création de ce compte, veuillez ignorer cet email.</p>
    </div>
    """

    data = {
        "sender": {"name": "Sunu-Villa Support", "email": "diallo30amadoukorka@gmail.com"},
        "to": [{"email": client_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {
        "api-key": SENDINBLUE_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
