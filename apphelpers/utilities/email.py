import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import html2text
from converge import settings

from apphelpers.loggers import app_logger


def format_msg(
    sender,
    recipients,
    subject,
    text=None,
    html=None,
    attachments=None,
    images=None,
    reply_to=None,
    bcc=None,
    headers=None,
):
    if html and not text:
        text = html2text.html2text(html)

    from_header = sender
    if isinstance(sender, (list, tuple)):
        from_header = formataddr(sender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = ", ".join(recipients)

    if bcc:
        msg["bcc"] = ", ".join(bcc)
    if reply_to:
        msg.add_header("reply-to", reply_to)

    msg.attach(MIMEText(text, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))
    if images:
        for cid, img in images:
            img_part = MIMEImage(img)
            img_part.add_header("Content-ID", "<" + cid + ">")
            msg.attach(img_part)
    if attachments:
        for file_path in attachments:
            file_name = os.path.basename(file_path)
            file_part = MIMEBase("application", "octet-stream")
            attachment = open(file_path, "rb")
            file_part.set_payload((attachment).read())
            encoders.encode_base64(file_part)
            file_part.add_header(
                "Content-Disposition", f"attachment; filename= {file_name}"
            )
            msg.attach(file_part)
    if headers:
        for key, value in headers.items():
            msg.add_header(key, value)
    return msg


def send_email(
    sender,
    recipients,
    subject,
    text=None,
    html=None,
    attachments=None,
    images=None,
    reply_to=None,
    bcc=None,
    headers=None,
):
    """
    text: text message. If html is provided and not text, text will be auto generated
    html: html message
    images: list of cid and image paths.
        eg. [('logo', 'images/logo.png'), ('Bruce', 'images/bat.png')]

    sender: can be sender email string e.g. 'foo@example.com' or
    list/tuple sender name and email  ('Foo', 'foo@example.com')
    headers: Dictionary of additional headers.
    """
    assert any((text, html)), "please provide html or text"

    if settings.DEBUG or settings.APP_MODE != "prod":
        # Make sure that we don't send emails to external emails in dev/stage
        filtered_recipients = []
        all_recipients = (tuple(recipients) + tuple(bcc)) if bcc else recipients
        for recpt in all_recipients:
            if isinstance(recpt, (list, tuple)):
                _, email = recpt
            else:
                email = recpt

            if any(
                email.endswith(f"@{domain}")
                for domain in settings.INTERNAL_EMAIL_DOMAINS
            ):
                filtered_recipients.append(recpt)
            else:
                internal_domains = ", ".join(settings.INTERNAL_EMAIL_DOMAINS)
                app_logger.info(
                    f"Skipping email to {email} as it does not end with any of"
                    f" {internal_domains}"
                )

        recipients = filtered_recipients

    msg = format_msg(
        sender,
        recipients,
        subject,
        text,
        html,
        attachments,
        images,
        reply_to,
        bcc,
        headers,
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=3) as s:
        if settings.SMTP_USERNAME:
            s.ehlo()
            s.starttls(context=context)
            s.login(settings.SMTP_USERNAME, settings.SMTP_KEY)

        s.send_message(msg=msg)
