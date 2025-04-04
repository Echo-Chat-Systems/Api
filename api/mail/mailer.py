"""
Contains the mailer class.
"""

# Standard Library Imports
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPServerDisconnected
from ssl import SSLContext, create_default_context

# Local Imports
from ..config import CONFIG

# Third Party Imports

# Constants
__all__ = [
    "Mailer",
]
CONTEXT: SSLContext = create_default_context()


class Mailer:
    """
    Sends emails.
    """
    __slots__ = [
        "connection",
    ]

    def __init__(self) -> None:
        """
        Initialize the mailer.
        """
        self.connection = SMTP(CONFIG.email.host, CONFIG.email.port)
        self.connection.starttls()
        self.connection.login(CONFIG.email.user, CONFIG.email.password)

    def __del__(self) -> None:
        """
        Delete the mailer.
        """
        try:
            self.connection.quit()
        except SMTPServerDisconnected:
            pass
        except AttributeError:
            pass

    def _send(
            self,
            to: str,
            subject: str,
            body: str
    ) -> None:
        """
        Send an email.

        Args:
            to (str): The email address to send to.
            subject (str): The subject of the email.
            body (str): The body of the email.

        Returns:
            None
        """
        # Create message
        message = MIMEMultipart()
        message["From"] = CONFIG.email.user
        message["To"] = to
        message["Subject"] = subject

        # Attach body
        message.attach(MIMEText(body, "plain"))

        # Send email
        self.connection.sendmail(CONFIG.email.user, to, message.as_string())

    def send_verification_code(
            self,
            user: str,
            code: str
    ) -> None:
        """
        Send a verification code.

        Args:
            user (str): The user's email address.
            code (str): The verification code.

        Returns:
            None
        """
        # Send email
        self._send(
            user,
            "Verify Your Email",
            f"""Someone is trying to register an account for you on an echo-api server named {CONFIG.server.name}. 
            
            If this was not you, you can safely ignore this email.
            
            If this was you, please click the following link to verify your email address and start using echo on this host: https://{CONFIG.server.host}/users/verify/{code}
            """
        )


