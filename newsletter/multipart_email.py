## Taken from http://www.rossp.org/blog/2007/oct/25/easy-multi-part-e-mails-django/ 
## but butchered a bit

from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_multipart_mail(text_part, html_part, subject, recipients,
                        sender=None, fail_silently=False):
    """
    This function will send a multi-part e-mail with both HTML and
    Text parts.

    template_name must NOT contain an extension. Both HTML (.html) and TEXT
        (.txt) versions must exist, eg 'emails/public_submit' will use both
        public_submit.html and public_submit.txt.

    email_context should be a plain python dictionary. It is applied against
        both the email messages (templates) & the subject.

    subject can be plain text or a Django template string, eg:
        New Job: {{ job.id }} {{ job.title }}

    recipients can be either a string, eg 'a@b.com' or a list, eg:
        ['a@b.com', 'c@d.com']. Type conversion is done if needed.

    sender can be an e-mail, 'Name <email>' or None. If unspecified, the
        DEFAULT_FROM_EMAIL will be used.

    """

    if not sender:
        sender = settings.DEFAULT_FROM_EMAIL

    if type(recipients) != list:
        recipients = [recipients,]

    msg = EmailMultiAlternatives(subject, text_part, sender, recipients)
    msg.attach_alternative(html_part, "text/html")
    return msg.send(fail_silently)
