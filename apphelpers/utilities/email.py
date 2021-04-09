import smtplib
import html2text

from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from converge import settings


def send_email(
    sender, recipients, subject, text=None, html=None,
    images=[], reply_to=None, bcc=None
):
    """
    text: text message. If html is provided and not text, text will be auto generated
    html: html message
    images: list of cid and image paths.
        eg. [('logo', 'images/logo.png'), ('Bruce', 'images/bat.png')]

    sender: can be sender email id e.g. 'abc@example.com' or combination of
    sender and its header (header can be name of email id owner or can be simply a
    text) e.g Honeybadger Notifications <tech@example.com>

    """
    assert any((text, html)), "please provide html or text"

    if html and not text:
        text = html2text.html2text(html)

    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    msg["From"] = formataddr(sender) if isinstance(sender, (list, tuple)) else sender
    msg["To"] = ', '.join(recipients)
    if bcc:
        msg["bcc"] = bcc
    if reply_to:
        msg.add_header("reply-to", reply_to)

    msg.attach(MIMEText(text, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))
    for cid, img in images:
        img_part = MIMEImage(img)
        img_part.add_header("Content-ID", "<" + cid + ">")
        msg.attach(img_part)

    s = smtplib.SMTP(settings.MD_HOST, settings.MD_PORT)
    if settings.MD_USERNAME:
        s.login(settings.MD_USERNAME, settings.MD_KEY)

    s.sendmail(sender, recipients, msg.as_string())

    s.quit()
