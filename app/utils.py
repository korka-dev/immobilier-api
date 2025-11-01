import os
from passlib.context import CryptContext
import httpx

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashed(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


# -------- HTML email templates --------

def email_template(title: str, content: str) -> str:
    """Generic styled HTML email template"""
    return f"""
    <div style="font-family: Arial, sans-serif; background-color: #f7f9fb; padding: 30px;">
      <div style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background-color: #2b6cb0; color: white; text-align: center; padding: 20px;">
          <h2 style="margin: 0;">🏡 Sunu-Villa Immobilier</h2>
          <p style="margin: 0; font-size: 14px;">{title}</p>
        </div>
        <div style="padding: 25px; color: #333333; line-height: 1.6;">
          {content}
        </div>
        <div style="background-color: #f0f4f8; text-align: center; padding: 15px; font-size: 13px; color: #666;">
          <p>© {2025} Sunu-Villa App. Tous droits réservés.</p>
        </div>
      </div>
    </div>
    """


# -------- Send Email functions --------

async def send_user_request_email(name: str, email: str, agence: str, contact: str):
    """Send email when user requests account creation"""
    api_key = os.getenv("SENDINBLUE_API_KEY")

    content = f"""
      <p><strong>Nom :</strong> {name}</p>
      <p><strong>Email :</strong> {email}</p>
      <p><strong>Agence :</strong> {agence or 'Non spécifiée'}</p>
      <p><strong>Contact :</strong> {contact or 'Non spécifié'}</p>
      <p style="margin-top: 20px;">Un nouvel utilisateur souhaite créer un compte sur <strong>Sunu-Villa App</strong>.</p>
    """

    html = email_template("Nouvelle demande de compte", content)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendinblue.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"email": "diallo30amadoukorka@gmail.com", "name": "Sunu-Villa App"},
                "to": [{"email": "diallo30amadoukorka@gmail.com"}],
                "subject": "📩 Nouvelle demande de compte – Sunu-Villa",
                "htmlContent": html
            }
        )
        response.raise_for_status()


async def send_account_created_email(client_email: str, client_name: str, password: str):
    """Send email to client with their credentials"""
    api_key = os.getenv("SENDINBLUE_API_KEY")

    content = f"""
      <p>Bonjour <strong>{client_name}</strong>,</p>
      <p>Votre compte a été créé avec succès sur <strong>Sunu-Villa Immobilier</strong>.</p>
      <p>Voici vos identifiants de connexion :</p>
      <ul style="background-color: #f8fafc; padding: 15px; border-radius: 8px; list-style: none;">
        <li><strong>Email :</strong> {client_email}</li>
        <li><strong>Mot de passe :</strong> {password}</li>
      </ul>
      <p style="margin-top: 10px;">👉 <em>Pensez à changer votre mot de passe après votre première connexion.</em></p>
      <p style="margin-top: 20px;">Merci de faire confiance à <strong>Sunu-Villa App</strong> !</p>
    """

    html = email_template("Bienvenue sur votre espace client 🌟", content)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendinblue.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"email": "diallo30amadoukorka@gmail.com", "name": "Sunu-Villa App"},
                "to": [{"email": client_email}],
                "subject": "🎉 Bienvenue sur Sunu-Villa Immobilier",
                "htmlContent": html
            }
        )
        response.raise_for_status()
