from django.core.mail import EmailMessage


def send_report_email(*, to_email: str, pdf_bytes: bytes) -> None:
    message = EmailMessage(
        subject="Your WattAmIUsing Electricity Cost Report",
        body=(
            "Hi,\n\n"
            "Thanks for your purchase! Your detailed electricity cost report is attached as a PDF.\n\n"
            "- WattAmIUsing\n"
            "https://watt-frontend.vercel.app/"
        ),
        to=[to_email],
    )
    message.attach("wattamiusing-report.pdf", pdf_bytes, "application/pdf")
    message.send(fail_silently=False)
