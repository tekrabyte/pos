import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_email = os.getenv('SMTP_EMAIL', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_name = os.getenv('STORE_NAME', 'QR Scan & Dine')
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP"""
        if not self.smtp_email or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email not sent.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.smtp_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, name: str, password: str) -> bool:
        """Send welcome email with auto-generated password"""
        subject = f"Selamat Datang di {self.from_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .password-box {{ background: white; border: 2px solid #10b981; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                .password {{ font-size: 24px; font-weight: bold; color: #10b981; letter-spacing: 2px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .button {{ background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍽️ Selamat Datang!</h1>
                </div>
                <div class="content">
                    <h2>Halo, {name}!</h2>
                    <p>Terima kasih telah mendaftar di <strong>{self.from_name}</strong>. Akun Anda telah berhasil dibuat!</p>
                    
                    <div class="password-box">
                        <p style="margin: 0; font-size: 14px; color: #666;">Password Anda:</p>
                        <p class="password">{password}</p>
                    </div>
                    
                    <p><strong>⚠️ Penting:</strong></p>
                    <ul>
                        <li>Simpan password ini dengan aman</li>
                        <li>Jangan bagikan password kepada siapapun</li>
                        <li>Anda dapat mengubah password setelah login</li>
                    </ul>
                    
                    <p>Email Anda: <strong>{to_email}</strong></p>
                    
                    <p>Sekarang Anda dapat mulai memesan makanan favorit Anda!</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">Mulai Belanja Sekarang</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Email ini dikirim otomatis, mohon tidak membalas email ini.</p>
                    <p>&copy; 2024 {self.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_password_reset_email(self, to_email: str, name: str, reset_token: str) -> bool:
        """Send password reset email"""
        # In production, this should be the actual frontend URL
        reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        subject = f"Reset Password - {self.from_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ background: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Reset Password</h1>
                </div>
                <div class="content">
                    <h2>Halo, {name}!</h2>
                    <p>Kami menerima permintaan untuk reset password akun Anda di <strong>{self.from_name}</strong>.</p>
                    
                    <p>Klik tombol di bawah ini untuk reset password Anda:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    
                    <p><strong>⚠️ Catatan:</strong></p>
                    <ul>
                        <li>Link ini hanya berlaku selama 1 jam</li>
                        <li>Jika Anda tidak meminta reset password, abaikan email ini</li>
                        <li>Untuk keamanan, jangan bagikan link ini kepada siapapun</li>
                    </ul>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 20px;">
                        Jika tombol tidak berfungsi, copy dan paste link berikut di browser Anda:<br>
                        <code>{reset_link}</code>
                    </p>
                </div>
                <div class="footer">
                    <p>Email ini dikirim otomatis, mohon tidak membalas email ini.</p>
                    <p>&copy; 2024 {self.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_new_password_email(self, to_email: str, name: str, new_password: str) -> bool:
        """Send new password email (admin reset)"""
        subject = f"Password Baru Anda - {self.from_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .password-box {{ background: white; border: 2px solid #3b82f6; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                .password {{ font-size: 24px; font-weight: bold; color: #3b82f6; letter-spacing: 2px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Baru</h1>
                </div>
                <div class="content">
                    <h2>Halo, {name}!</h2>
                    <p>Password akun Anda di <strong>{self.from_name}</strong> telah direset oleh admin.</p>
                    
                    <div class="password-box">
                        <p style="margin: 0; font-size: 14px; color: #666;">Password Baru Anda:</p>
                        <p class="password">{new_password}</p>
                    </div>
                    
                    <p><strong>⚠️ Penting:</strong></p>
                    <ul>
                        <li>Gunakan password ini untuk login</li>
                        <li>Disarankan untuk mengubah password setelah login</li>
                        <li>Jangan bagikan password kepada siapapun</li>
                    </ul>
                    
                    <p>Email Anda: <strong>{to_email}</strong></p>
                </div>
                <div class="footer">
                    <p>Email ini dikirim otomatis, mohon tidak membalas email ini.</p>
                    <p>&copy; 2024 {self.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

# Create singleton instance
email_service = EmailService()
